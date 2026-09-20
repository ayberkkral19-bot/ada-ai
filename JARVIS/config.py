import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env'))

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', '')
GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
VOICE_ID_MALE = os.getenv('VOICE_ID_MALE', 'c1An0BcfdBgMtEqajijL')
VOICE_ID_FEMALE = os.getenv('VOICE_ID_FEMALE', 'mnEe2Jhwlupp6oZEDi3k')
WAKE_WORD = os.getenv('WAKE_WORD', 'hey jarvis')
DEFAULT_LANGUAGE = os.getenv('DEFAULT_LANGUAGE', 'tr-TR')
TTS_ENGINE = os.getenv('TTS_ENGINE', 'elevenlabs')

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarvis_memory.db')

WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700

COLORS = {
    'bg_dark': '#0a0e1a',
    'bg_mid': '#111827',
    'bg_light': '#1f2937',
    'accent_blue': '#00f0ff',
    'accent_orange': '#ff9900',
    'accent_gold': '#ffe600',
    'accent_green': '#00ff88',
    'accent_red': '#ff3344',
    'accent_purple': '#a855f7',
    'text_primary': '#e5e7eb',
    'text_secondary': '#9ca3af',
    'text_dim': '#6b7280',
    'border': '#374151',
    'grid_line': '#1e293b',
}

APP_NAME = 'J.A.R.V.I.S.'
APP_VERSION = '6.5'
APP_SUBTITLE = 'UNIVERSAL COGNITIVE OS & CORE ACCELERATOR'

BOOT_MESSAGES = [
    'Initializing J.A.R.V.I.S. kernel...',
    'Loading core modules...',
    'Starting AI decision engine...',
    'Connecting to Groq API...',
    'Initializing ElevenLabs voice motor...',
    'Loading system control modules...',
    'Starting telemetry monitors...',
    'Initializing memory subsystem...',
    'Calibrating speech recognition...',
    'Loading STT/TTS pipelines...',
    'System identification: TONY STARK...',
    'All systems nominal.',
    'J.A.R.V.I.S. ONLINE.',
]

KNOWN_APPS = {
    'chrome': 'chrome',
    'google chrome': 'chrome',
    'firefox': 'firefox',
    'spotify': 'spotify',
    'vs code': 'code',
    'vscode': 'code',
    'visual studio code': 'code',
    'notepad': 'notepad',
    'hesap makinesi': 'calc',
    'calculator': 'calc',
    'paint': 'mspaint',
    'discord': 'discord',
    'terminal': 'cmd',
    'cmd': 'cmd',
    'powershell': 'powershell',
    'explorer': 'explorer',
    'file manager': 'explorer',
    'word': 'winword',
    'excel': 'excel',
    'powerpoint': 'powerpnt',
    'teams': 'ms-teams',
    'zoom': 'zoom',
    'steam': 'steam',
    'epic': 'epicgameslauncher',
}

WEATHER_API_URL = 'https://api.openweathermap.org/data/2.5/weather'

STT_ENERGY_THRESHOLD = 4000
STT_PAUSE_THRESHOLD = 1.0
STT_PHRASE_TIME_LIMIT = 10
