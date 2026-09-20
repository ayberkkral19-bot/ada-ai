import os
import subprocess
import webbrowser
import ctypes
import platform
import re
from datetime import datetime
import requests
import psutil

try:
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
    from comtypes import CLSCTX_ALL
    HAS_PYCAW = True
except ImportError:
    HAS_PYCAW = False

try:
    import pyautogui
    HAS_PYAUTOGUI = True
except ImportError:
    HAS_PYAUTOGUI = False

from config import KNOWN_APPS, WEATHER_API_URL


class SystemControl:
    def __init__(self):
        self._volume = None
        if HAS_PYCAW:
            try:
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                self._volume = interface.QueryInterface(IAudioEndpointVolume)
            except Exception:
                self._volume = None

    def open_application(self, app_name):
        app_name_lower = app_name.lower().strip()
        for key, cmd in KNOWN_APPS.items():
            if key in app_name_lower:
                try:
                    subprocess.Popen(cmd, shell=True)
                    return True, f'{app_name} başarıyla açıldı.'
                except Exception as e:
                    return False, f'{app_name} açılamadı: {e}'
        try:
            os.startfile(app_name)
            return True, f'{app_name} açıldı.'
        except Exception:
            pass
        try:
            subprocess.Popen(f'start {app_name}', shell=True)
            return True, f'{app_name} açılmaya çalışılıyor.'
        except Exception as e:
            return False, f'{app_name} bulunamadı veya açılamadı: {e}'

    def close_application(self, app_name):
        app_name_lower = app_name.lower().strip()
        for key, cmd in KNOWN_APPS.items():
            if key in app_name_lower:
                try:
                    os.system(f'taskkill /f /im {cmd}.exe 2>nul')
                    return True, f'{app_name} kapatıldı.'
                except Exception as e:
                    return False, f'{app_name} kapatılamadı: {e}'
        try:
            os.system(f'taskkill /f /im {app_name}.exe 2>nul')
            return True, f'{app_name} kapatılmaya çalışıldı.'
        except Exception as e:
            return False, f'{app_name} kapatılamadı: {e}'

    def get_volume(self):
        if self._volume:
            try:
                vol = self._volume.GetMasterVolumeLevelScalar()
                return int(vol * 100)
            except Exception:
                return 0
        return 0

    def set_volume(self, level):
        level = max(0, min(100, level))
        if self._volume:
            try:
                self._volume.SetMasterVolumeLevelScalar(level / 100.0, None)
                return True, f'Ses seviyesi %{level} olarak ayarlandı.'
            except Exception as e:
                return False, f'Ses ayarlanamadı: {e}'
        return False, 'Ses kontrolü mevcut değil.'

    def increase_volume(self, amount=10):
        current = self.get_volume()
        return self.set_volume(current + amount)

    def decrease_volume(self, amount=10):
        current = self.get_volume()
        return self.set_volume(current - amount)

    def mute_volume(self):
        if self._volume:
            try:
                self._volume.SetMute(1, None)
                return True, 'Ses sessize alındı.'
            except Exception as e:
                return False, f'Sessize alma hatası: {e}'
        return False, 'Ses kontrolü mevcut değil.'

    def unmute_volume(self):
        if self._volume:
            try:
                self._volume.SetMute(0, None)
                return True, 'Ses açıldı.'
            except Exception as e:
                return False, f'Ses açma hatası: {e}'
        return False, 'Ses kontrolü mevcut değil.'

    def get_current_time(self):
        now = datetime.now()
        return now.strftime('%H:%M')

    def get_current_date(self):
        now = datetime.now()
        months_tr = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
                      'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık']
        days_tr = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi', 'Pazar']
        day_name = days_tr[now.weekday()]
        month_name = months_tr[now.month - 1]
        return f'{day_name}, {now.day} {month_name} {now.year}'

    def get_time_report(self):
        now = datetime.now()
        return f'Su an saat {self.get_current_time()}, {self.get_current_date()}.'

    def open_website(self, url):
        if not url.startswith('http'):
            url = 'https://' + url
        try:
            webbrowser.open(url)
            return True, f'{url} adresi açıldı.'
        except Exception as e:
            return False, f'Site açılamadı: {e}'

    def search_google(self, query):
        url = f'https://www.google.com/search?q={query}'
        try:
            webbrowser.open(url)
            return True, f'Google\'da "{query}" araması yapılıyor.'
        except Exception as e:
            return False, f'Arama yapılamadı: {e}'

    def open_youtube_search(self, query):
        url = f'https://www.youtube.com/results?search_query={query}'
        try:
            webbrowser.open(url)
            return True, f'YouTube\'da "{query}" aranıyor.'
        except Exception as e:
            return False, f'YouTube araması yapılamadı: {e}'

    def take_screenshot(self, path=None):
        if not HAS_PYAUTOGUI:
            return False, 'PyAutoGUI yüklü değil.'
        try:
            if path is None:
                path = os.path.join(os.path.expanduser('~'), 'Desktop', f'screenshot_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png')
            screenshot = pyautogui.screenshot()
            screenshot.save(path)
            return True, f'Ekran görüntüsü kaydedildi: {path}'
        except Exception as e:
            return False, f'Ekran görüntüsü alınamadı: {e}'

    def shutdown_pc(self):
        try:
            if platform.system() == 'Windows':
                os.system('shutdown /s /t 60')
            else:
                os.system('shutdown -h +1')
            return True, 'Bilgisayar 1 dakika içinde kapatılacak.'
        except Exception as e:
            return False, f'Kapatma hatası: {e}'

    def restart_pc(self):
        try:
            if platform.system() == 'Windows':
                os.system('shutdown /r /t 60')
            else:
                os.system('reboot')
            return True, 'Bilgisayar 1 dakika içinde yeniden başlatılacak.'
        except Exception as e:
            return False, f'Yeniden başlatma hatası: {e}'

    def sleep_pc(self):
        try:
            if platform.system() == 'Windows':
                os.system('rundll32.exe powrprof.dll,SetSuspendState 0,1,0')
            else:
                os.system('systemctl suspend')
            return True, 'Bilgisayar uyku moduna alınıyor.'
        except Exception as e:
            return False, f'Uyku modu hatası: {e}'

    def cancel_shutdown(self):
        try:
            os.system('shutdown /a')
            return True, 'Kapatma iptal edildi.'
        except Exception as e:
            return False, f'İptal hatası: {e}'

    def get_weather(self, city='Istanbul', api_key=''):
        if not api_key:
            return None, 'Hava durumu API anahtarı ayarlanmamış.'
        try:
            params = {
                'q': city,
                'appid': api_key,
                'units': 'metric',
                'lang': 'tr'
            }
            resp = requests.get(WEATHER_API_URL, params=params, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                temp = data['main']['temp']
                feels = data['main']['feels_like']
                desc = data['weather'][0]['description']
                humidity = data['main']['humidity']
                wind = data['wind']['speed']
                report = (
                    f'{city} hava durumu: {desc.capitalize()}, '
                    f'sıcaklık {temp:.0f} derece (hissedilen {feels:.0f}), '
                    f'rutubet %{humidity}, rüzgar {wind:.1f} m/s.'
                )
                return True, report
            else:
                return False, f'Hava durumu alınamadı: HTTP {resp.status_code}'
        except Exception as e:
            return False, f'Hava durumu hatası: {e}'

    def get_weather_no_api(self, city='Istanbul'):
        try:
            query = f'{city} hava durumu'
            url = f'https://wttr.in/{city}?format=%C+%t+%h+%w&lang=tr'
            resp = requests.get(url, timeout=10, headers={'User-Agent': 'curl/7.68.0'})
            if resp.status_code == 200:
                return True, f'{city} hava durumu: {resp.text.strip()}'
            return False, 'Hava durumu alınamadı.'
        except Exception as e:
            return False, f'Hava durumu hatası: {e}'

    def handle_command(self, text):
        lower = text.lower().strip()

        if any(kw in lower for kw in ['saat kaç', 'saati söyle', 'saat ne', 'şu an saat']):
            return True, self.get_time_report()

        if any(kw in lower for kw in ['bugün ne', 'bugünün tarihi', 'tarih ne', 'hangi gün']):
            return True, self.get_current_date()

        if any(kw in lower for kw in ['hava durumu', 'hava nasıl', 'dışarıda hava']):
            city_match = re.search(r'(?:hava durumu|dışarıda hava)\s+(?:nasıl|ne|olduğunda)?\s*(\w+)', lower)
            city = city_match.group(1).capitalize() if city_match else 'Istanbul'
            success, report = self.get_weather_no_api(city)
            return success, report

        if any(kw in lower for kw in ['sesi aç', 'ses aç', 'sesi yükselt']):
            amt_match = re.search(r'(\d+)', lower)
            amt = int(amt_match.group(1)) if amt_match else 10
            return self.increase_volume(amt)

        if any(kw in lower for kw in ['sesi kıs', 'ses kıs', 'sesi azalt']):
            amt_match = re.search(r'(\d+)', lower)
            amt = int(amt_match.group(1)) if amt_match else 10
            return self.decrease_volume(amt)

        if any(kw in lower for kw in ['sessiz', 'sessize al', 'mute']):
            return self.mute_volume()

        if any(kw in lower for kw in ['sesi aç sesi', 'unmute', 'sessizliği']):
            return self.unmute_volume()

        vol_match = re.search(r'ses[şi]\s*(\d+)\s*(?:yap|ayarla|ol)', lower)
        if vol_match:
            level = int(vol_match.group(1))
            return self.set_volume(level)

        if any(kw in lower for kw in ['bilgisayarı kapat', 'pc kapat', 'bilgisayarı kapat', 'kapat']):
            if 'yeniden' in lower or 'başlat' in lower or 'reboot' in lower:
                return self.restart_pc()
            if 'uyku' in lower or 'uyut' in lower or 'sleep' in lower:
                return self.sleep_pc()
            return self.shutdown_pc()

        if any(kw in lower for kw in ['yeniden başlat', 'reboot', 'restart']):
            return self.restart_pc()

        if any(kw in lower for kw in ['uyku modu', 'uyut', 'sleep']):
            return self.sleep_pc()

        if any(kw in lower for kw in ['kapatmayı iptal', 'shutdown cancel']):
            return self.cancel_shutdown()

        if any(kw in lower for kw in ['ekran görüntüsü', 'screenshot', 'ekran resmi']):
            return self.take_screenshot()

        if any(kw in lower for kw in ['sistem durumu', 'sistem raporu', 'bilgisayar nasıl', 'donanım']):
            return True, self.get_weather_report_text()

        return False, None

    def get_weather_report_text(self):
        cpu = psutil.cpu_percent(interval=0.5)
        mem = psutil.virtual_memory()
        bat = psutil.sensors_battery()
        bat_str = f'Batarya: %{bat.percent:.0f}' if bat else 'Batarya: Masaüstü'
        return (
            f'Sistem durumu: CPU %{cpu:.1f}, RAM %{mem.percent:.1f} '
            f'({mem.used / (1024**3):.1f}/{mem.total / (1024**3):.1f} GB), {bat_str}.'
        )

    def handle_app_command(self, text):
        lower = text.lower().strip()

        open_patterns = [
            r'(?:aç|ac|başlat|baslat|çalıştır|calistir)\s+(.+)',
            r'(.+?)\s+(?:aç|ac|başlat|baslat)',
        ]
        close_patterns = [
            r'(?:kapat|durdur|sonlandır|sonlandir)\s+(.+)',
            r'(.+?)\s+(?:kapat|durdur)',
        ]

        for pattern in open_patterns:
            match = re.search(pattern, lower)
            if match:
                app = match.group(1).strip()
                return self.open_application(app)

        for pattern in close_patterns:
            match = re.search(pattern, lower)
            if match:
                app = match.group(1).strip()
                return self.close_application(app)

        return False, None

    def handle_web_command(self, text):
        lower = text.lower().strip()

        if any(kw in lower for kw in ['youtube', 'youtube\'da']):
            query_match = re.search(r'youtube\'?da?\s+(.+?)(?:\s+(?:izle|başlat|aç))?\s*$', lower)
            if query_match:
                return self.open_youtube_search(query_match.group(1).strip())
            return self.open_website('youtube.com')

        if any(kw in lower for kw in ['google\'da ara', 'google ara', 'internette ara', 'web\'de ara']):
            query_match = re.search(r'(?:google|internette|web\'?de)\s+ara[ycz]?\s+(.+)', lower)
            if query_match:
                return self.search_google(query_match.group(1).strip())

        if any(kw in lower for kw in ['instagram', 'insta']):
            if 'mesaj' in lower or 'dm' in lower:
                return self.open_website('https://www.instagram.com/direct/inbox/')
            return self.open_website('instagram.com')

        if 'github' in lower:
            return self.open_website('github.com')

        if 'discord' in lower:
            return self.open_website('discord.com/app')

        if 'spotify' in lower:
            return self.open_website('open.spotify.com')

        if 'wikipedia' in lower or 'vikipedi' in lower:
            wiki_match = re.search(r'(?:wikipedia|vikipedi)\s+(.+)', lower)
            if wiki_match:
                return self.open_website(f'https://tr.wikipedia.org/wiki/{wiki_match.group(1).strip()}')
            return self.open_website('wikipedia.org')

        if any(kw in lower for kw in ['twitter', 'x.com']):
            return self.open_website('x.com')

        if 'tiktok' in lower:
            return self.open_website('tiktok.com')

        if 'reddit' in lower:
            return self.open_website('reddit.com')

        if 'facebook' in lower:
            return self.open_website('facebook.com')

        if 'netflix' in lower:
            return self.open_website('netflix.com')

        if 'steam' in lower:
            return self.open_website('store.steampowered.com')

        url_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', lower)
        if url_match:
            return self.open_website(url_match.group(1))

        return False, None
