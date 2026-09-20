import PyInstaller.__main__
import os

PyInstaller.__main__.run([
    'main.py',
    '--name=J.A.R.V.I.S.',
    '--onefile',
    '--windowed',
    '--noconfirm',
    '--clean',
    '--hidden-import=customtkinter',
    '--hidden-import=PyAudio',
    '--hidden-import=speech_recognition',
    '--hidden-import=edge_tts',
    '--hidden-import=pyttsx3',
    '--hidden-import=psutil',
    '--hidden-import=pycaw',
    '--hidden-import=pyautogui',
    '--hidden-import=elevenlabs',
    '--hidden-import=groq',
    '--hidden-import=sounddevice',
    '--hidden-import=soundfile',
    '--hidden-import=numpy',
    '--hidden-import=requests',
    '--hidden-import=comtypes',
    '--collect-data=customtkinter',
])
