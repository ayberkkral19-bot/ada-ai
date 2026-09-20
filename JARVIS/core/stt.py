import threading
import queue
import time

try:
    import speech_recognition as sr
    HAS_SR = True
except ImportError:
    HAS_SR = False

try:
    import pyaudio
    HAS_PYAUDIO = True
except ImportError:
    HAS_PYAUDIO = False

from config import (
    STT_ENERGY_THRESHOLD,
    STT_PAUSE_THRESHOLD,
    STT_PHRASE_TIME_LIMIT,
    DEFAULT_LANGUAGE,
    WAKE_WORD,
)


class STT:
    def __init__(self, language=None):
        self.language = language or DEFAULT_LANGUAGE
        self.is_listening = False
        self._callback = None
        self._wake_callback = None
        self._recognizer = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._result_queue = queue.Queue()
        self._thread = None
        self.wake_word = WAKE_WORD

        if HAS_SR:
            self._recognizer = sr.Recognizer()
            self._recognizer.energy_threshold = STT_ENERGY_THRESHOLD
            self._recognizer.dynamic_energy_threshold = True
            self._recognizer.pause_threshold = STT_PAUSE_THRESHOLD

    def get_microphone_list(self):
        if not HAS_SR:
            return []
        try:
            mics = sr.Microphone.list_microphone_names()
            return [(i, name) for i, name in enumerate(mics)]
        except Exception:
            return []

    def set_callback(self, callback):
        self._callback = callback

    def set_wake_callback(self, callback):
        self._wake_callback = callback

    def start_listening(self, continuous=True):
        if not HAS_SR:
            print('[STT] SpeechRecognition yüklü değil.')
            return False
        if self.is_listening:
            return True

        self.is_listening = True
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._listen_loop,
            args=(continuous,),
            daemon=True
        )
        self._thread.start()
        return True

    def stop_listening(self):
        self.is_listening = False
        self._stop_event.set()

    def get_result(self, timeout=0.1):
        try:
            return self._result_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def _listen_loop(self, continuous):
        while self.is_listening and not self._stop_event.is_set():
            try:
                with sr.Microphone() as source:
                    self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                    try:
                        audio = self._recognizer.listen(
                            source,
                            timeout=3,
                            phrase_time_limit=STT_PHRASE_TIME_LIMIT
                        )
                    except sr.WaitTimeoutError:
                        continue

                    try:
                        text = self._recognizer.recognize_google(audio, language=self.language)
                        if text and text.strip():
                            text = text.strip()
                            self._result_queue.put(('final', text))
                            lower = text.lower()
                            if self.wake_word.lower() in lower:
                                after_wake = text
                                for kw in [self.wake_word, 'hey jarvis', 'hey jARVIS']:
                                    after_wake = after_wake.replace(kw, '').strip()
                                if self._wake_callback:
                                    self._wake_callback(after_wake if after_wake else None)
                                elif self._callback:
                                    self._callback(after_wake if after_wake else 'Dinliyorum.', 'final')
                            elif self._callback:
                                self._callback(text, 'final')
                    except sr.UnknownValueError:
                        pass
                    except sr.RequestError as e:
                        self._result_queue.put(('error', f'Ses tanıma servis hatası: {e}'))
                    except Exception as e:
                        self._result_queue.put(('error', f'Ses tanıma hatası: {e}'))

            except sr.WaitTimeoutError:
                continue
            except OSError as e:
                print(f'[STT] Mikrofon hatası: {e}')
                self._result_queue.put(('error', f'Mikrofon hatası: {e}'))
                time.sleep(1)
            except Exception as e:
                print(f'[STT] Dinleme hatası: {e}')
                time.sleep(0.5)

            if not continuous:
                break

    def listen_once(self, timeout=5, phrase_limit=10):
        if not HAS_SR:
            return None, 'SpeechRecognition yüklü değil.'
        try:
            with sr.Microphone() as source:
                self._recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = self._recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                try:
                    text = self._recognizer.recognize_google(audio, language=self.language)
                    return text, None
                except sr.UnknownValueError:
                    return None, 'Anlaşılamadı.'
                except sr.RequestError as e:
                    return None, f'Ses tanıma servis hatası: {e}'
        except sr.WaitTimeoutError:
            return None, 'Ses algılanamadı.'
        except Exception as e:
            return None, f'Mikrofon hatası: {e}'
