import sys
import os
import threading
import time
import queue

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui.app import JarvisHUD
from core.memory import Memory
from core.telemetry import Telemetry
from core.system_control import SystemControl
from core.tts import TTS
from core.stt import STT
from core.brain import Brain


class JarvisCore:
    def __init__(self):
        self.memory = Memory()
        self.telemetry = Telemetry()
        self.sysctl = SystemControl()
        self.tts = TTS(engine='edge')
        self.stt = STT()
        self.brain = Brain()
        self.gui = None
        self._running = False

    def start(self):
        self.gui = JarvisHUD()
        self._running = True
        self.stt.set_callback(self._on_speech_result)
        self.stt.set_wake_callback(self._on_wake_word)
        self.gui.after(500, self._init_mics)
        self.gui.after(200, self._process_gui_queue)
        self.gui.protocol('WM_DELETE_WINDOW', self._on_close)
        self.gui.mainloop()

    def _init_mics(self):
        mics = self.stt.get_microphone_list()
        self.gui.receive_mic_list(mics)

    def _process_gui_queue(self):
        if not self._running:
            return
        try:
            while True:
                action, data = self.gui.input_queue.get_nowait()
                if action == 'process_input':
                    t = threading.Thread(target=self._handle_input, args=(data,), daemon=True)
                    t.start()
                elif action == 'start_listening':
                    self.stt.start_listening(continuous=True)
                    self.gui.receive_status('listening')
                elif action == 'stop_listening':
                    self.stt.stop_listening()
                    self.gui.receive_status('idle')
        except queue.Empty:
            pass
        self.gui.after(50, self._process_gui_queue)

    def _on_speech_result(self, text, result_type):
        if result_type == 'error':
            self.gui.receive_system_message(f'Ses tanima hatasi: {text}')
            return
        if result_type == 'final' and text:
            self.gui.receive_status('thinking')
            t = threading.Thread(target=self._handle_input, args=(text,), daemon=True)
            t.start()

    def _on_wake_word(self, after_wake):
        if after_wake:
            self.gui.receive_status('thinking')
            t = threading.Thread(target=self._handle_input, args=(after_wake,), daemon=True)
            t.start()
        else:
            self.gui.after(0, lambda: self._speak_async('Evet efendim, sizi dinliyorum.'))
            self.gui.receive_status('listening')

    def _handle_input(self, text):
        try:
            self.memory.save_message('user', text)
            self.gui.receive_thinking_start()
            self.gui.receive_status('thinking')
            intents = self.brain.classify_intent(text)
            primary_intent = intents[0]

            local_handlers = {
                'app_control': self.sysctl.handle_app_command,
                'volume_control': self.sysctl.handle_command,
                'time_info': self.sysctl.handle_command,
                'weather': self.sysctl.handle_command,
                'power_control': self.sysctl.handle_command,
                'web_control': self.sysctl.handle_web_command,
                'screenshot': self.sysctl.handle_command,
                'system_info': self.sysctl.handle_command,
            }

            if primary_intent in local_handlers:
                handler = local_handlers[primary_intent]
                success, result = handler(text)
                if result:
                    self.gui.receive_thinking_end()
                    self.gui.receive_response(result)
                    self.memory.save_message('assistant', result)
                    self.memory.log_command(text, result, success)
                    self._speak_async(result)
                    return

            self.gui.receive_thinking_end()
            messages = [{'role': m['role'], 'content': m['content']} for m in self.memory.get_history(20)]
            if not messages or messages[-1].get('content') != text:
                messages.append({'role': 'user', 'content': text})

            def on_brain_response(reply):
                self.gui.receive_response(reply)
                self.memory.save_message('assistant', reply)
                self._speak_async(reply)

            self.brain.chat_async(messages, callback=on_brain_response)

        except Exception as e:
            self.gui.receive_thinking_end()
            error_msg = f'Hata olustu: {str(e)}'
            self.gui.receive_response(error_msg)
            self.gui.receive_status('error')
            self.gui.after(3000, lambda: self.gui.receive_status('idle'))

    def _speak_async(self, text):
        def _worker():
            self.gui.receive_status('speaking')
            self.tts.is_speaking = True
            import math
            t = 0
            while self.tts.is_speaking:
                amp = (math.sin(t * 0.1) + 1) / 2 * 0.5 + 0.3
                self.gui.receive_speaking_amp(amp)
                t += 1
                time.sleep(0.1)
            self.gui.receive_speaking_amp(0)
            self.gui.receive_status('idle')
        threading.Thread(target=_worker, daemon=True).start()
        self.tts.speak(text)

    def _on_close(self):
        self._running = False
        self.stt.stop_listening()
        self.tts.stop()
        try:
            self.gui.destroy()
        except Exception:
            pass
        os._exit(0)


def main():
    app = JarvisCore()
    app.start()


if __name__ == '__main__':
    main()
