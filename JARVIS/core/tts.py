import threading
import queue
import os
import tempfile
import asyncio

try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    import pyttsx3
    HAS_PYTTSX3 = True
except ImportError:
    HAS_PYTTSX3 = False

try:
    import sounddevice as sd
    import soundfile as sf
    HAS_SOUND = True
except ImportError:
    HAS_SOUND = False

from config import ELEVENLABS_API_KEY, VOICE_ID_MALE, VOICE_ID_FEMALE

try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import play as el_play
    from elevenlabs.api import Audio as ElAudio
    HAS_ELEVENLABS = True
except ImportError:
    HAS_ELEVENLABS = False


class TTS:
    def __init__(self, engine='edge'):
        self.engine = engine
        self.voice_id = VOICE_ID_MALE
        self.is_speaking = False
        self._queue = queue.Queue()
        self._worker_thread = None
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._pyttsx3 = None
        if HAS_PYTTSX3:
            try:
                self._pyttsx3 = pyttsx3.init()
                voices = self._pyttsx3.getProperty('voices')
                for v in voices:
                    if 'turkish' in v.name.lower() or 'tr' in v.id.lower():
                        self._pyttsx3.setProperty('voice', v.id)
                        break
                self._pyttsx3.setProperty('rate', 160)
                self._pyttsx3.setProperty('volume', 1.0)
            except Exception:
                self._pyttsx3 = None
        self._start_worker()

    def _start_worker(self):
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()

    def _process_queue(self):
        while True:
            try:
                text, callback = self._queue.get(timeout=1)
                self._do_speak(text)
                if callback:
                    callback()
                self._queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                print(f'[TTS] Queue error: {e}')

    def set_voice(self, voice_key):
        if voice_key == 'kadin' or voice_key == 'female':
            self.voice_id = VOICE_ID_FEMALE
        else:
            self.voice_id = VOICE_ID_MALE

    def speak(self, text, callback=None):
        if not text or not text.strip():
            return
        self._queue.put((text.strip(), callback))

    def stop(self):
        self._stop_event.set()
        self.is_speaking = False
        try:
            if HAS_SOUND:
                sd.stop()
        except Exception:
            pass

    def _do_speak(self, text):
        self.is_speaking = True
        self._stop_event.clear()
        try:
            if self.engine == 'elevenlabs' and HAS_ELEVENLABS and ELEVENLABS_API_KEY:
                self._speak_elevenlabs(text)
            elif self.engine == 'edge' and HAS_EDGE_TTS:
                self._speak_edge(text)
            elif HAS_PYTTSX3 and self._pyttsx3:
                self._speak_pyttsx3(text)
            else:
                self._speak_fallback(text)
        except Exception as e:
            print(f'[TTS] Speak error: {e}')
        finally:
            self.is_speaking = False

    def _speak_elevenlabs(self, text):
        try:
            client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            audio_iterator = client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text[:5000],
                model_id='eleven_multilingual_v2',
                voice_settings={
                    'stability': 0.65,
                    'similarity_boost': 0.85,
                    'style': 0.15,
                    'use_speaker_boost': True
                }
            )
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            for chunk in audio_iterator:
                if isinstance(chunk, bytes):
                    tmp.write(chunk)
                elif isinstance(chunk, str):
                    pass
            tmp.close()
            if HAS_SOUND:
                try:
                    data, samplerate = sf.read(tmp.name)
                    sd.play(data, samplerate)
                    sd.wait()
                except Exception:
                    os.system(f'start "" "{tmp.name}"')
            else:
                os.system(f'start "" "{tmp.name}"')
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
        except Exception as e:
            print(f'[TTS] ElevenLabs error: {e}')
            self._speak_pyttsx3(text)

    def _speak_edge(self, text):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            voice = 'tr-TR-AhmetNeural' if self.voice_id == VOICE_ID_MALE else 'tr-TR-EmelNeural'
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tmp.close()

            async def _gen():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(tmp.name)

            loop.run_until_complete(_gen())

            if HAS_SOUND:
                try:
                    data, samplerate = sf.read(tmp.name)
                    sd.play(data, samplerate)
                    sd.wait()
                except Exception:
                    os.system(f'start "" "{tmp.name}"')
            else:
                os.system(f'start "" "{tmp.name}"')
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
            loop.close()
        except Exception as e:
            print(f'[TTS] Edge-TTS error: {e}')
            self._speak_pyttsx3(text)

    def _speak_pyttsx3(self, text):
        if self._pyttsx3:
            try:
                self._pyttsx3.say(text)
                self._pyttsx3.runAndWait()
            except Exception as e:
                print(f'[TTS] pyttsx3 error: {e}')
                self._speak_fallback(text)
        else:
            self._speak_fallback(text)

    def _speak_fallback(self, text):
        print(f'[TTS] Ses motoru mevcut değil. Metin: {text[:100]}...')
