import psutil
import platform
import os
from datetime import datetime, timezone


class Telemetry:
    def __init__(self):
        self._prev_cpu = None

    def get_cpu_usage(self):
        try:
            usage = psutil.cpu_percent(interval=0.5)
            count = psutil.cpu_count(logical=True)
            freq = psutil.cpu_freq()
            freq_current = freq.current if freq else 0
            return {
                'percent': usage,
                'cores': count,
                'freq_mhz': round(freq_current, 0),
                'label': f'CPU: %{usage:.1f} ({count} cores)'
            }
        except Exception as e:
            return {'percent': 0, 'cores': 0, 'freq_mhz': 0, 'label': f'CPU: Hata - {e}'}

    def get_memory_info(self):
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return {
                'total_gb': round(mem.total / (1024**3), 2),
                'used_gb': round(mem.used / (1024**3), 2),
                'available_gb': round(mem.available / (1024**3), 2),
                'percent': mem.percent,
                'swap_percent': swap.percent,
                'label': f'RAM: %{mem.percent:.1f} ({mem.used / (1024**3):.1f}/{mem.total / (1024**3):.1f} GB)'
            }
        except Exception as e:
            return {'total_gb': 0, 'used_gb': 0, 'available_gb': 0, 'percent': 0, 'swap_percent': 0, 'label': f'RAM: Hata - {e}'}

    def get_disk_info(self):
        try:
            partitions = []
            for part in psutil.disk_partitions():
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        'device': part.device,
                        'mountpoint': part.mountpoint,
                        'total_gb': round(usage.total / (1024**3), 2),
                        'used_gb': round(usage.used / (1024**3), 2),
                        'free_gb': round(usage.free / (1024**3), 2),
                        'percent': usage.percent
                    })
                except PermissionError:
                    continue
            primary = partitions[0] if partitions else {}
            label = f'Disk: %{primary.get("percent", 0):.1f} ({primary.get("used_gb", 0):.1f}/{primary.get("total_gb", 0):.1f} GB)' if primary else 'Disk: Bilgi yok'
            return {'partitions': partitions, 'primary': primary, 'label': label}
        except Exception as e:
            return {'partitions': [], 'primary': {}, 'label': f'Disk: Hata - {e}'}

    def get_battery_info(self):
        try:
            bat = psutil.sensors_battery()
            if bat is None:
                return {'percent': 100, 'plugged': True, 'secs_left': 0, 'label': 'Batarya: Masaüstü (Pil yok)'}
            secs = bat.secsleft
            if secs == psutil.POWER_TIME_UNLIMITED:
                time_str = 'Şarjda'
            elif secs == psutil.POWER_TIME_UNKNOWN:
                time_str = 'Bilinmiyor'
            else:
                hours = secs // 3600
                mins = (secs % 3600) // 60
                time_str = f'{hours}sa {mins}dk'
            return {
                'percent': bat.percent,
                'plugged': bat.power_plugged,
                'secs_left': secs,
                'time_str': time_str,
                'label': f'Batarya: %{bat.percent:.0f} {"(Şarjda)" if bat.power_plugged else time_str}'
            }
        except Exception as e:
            return {'percent': 0, 'plugged': False, 'secs_left': 0, 'time_str': 'Hata', 'label': f'Batarya: Hata - {e}'}

    def get_network_info(self):
        try:
            net = psutil.net_io_counters()
            return {
                'bytes_sent': net.bytes_sent,
                'bytes_recv': net.bytes_recv,
                'sent_gb': round(net.bytes_sent / (1024**3), 2),
                'recv_gb': round(net.bytes_recv / (1024**3), 2),
                'label': f'Ağ: ↑{net.bytes_sent / (1024**2):.1f} MB ↓{net.bytes_recv / (1024**2):.1f} MB'
            }
        except Exception as e:
            return {'bytes_sent': 0, 'bytes_recv': 0, 'sent_gb': 0, 'recv_gb': 0, 'label': f'Ağ: Hata - {e}'}

    def get_system_info(self):
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = datetime.now() - boot_time
            hours = int(uptime.total_seconds() // 3600)
            mins = int((uptime.total_seconds() % 3600) // 60)
            return {
                'os': platform.system(),
                'os_version': platform.version(),
                'machine': platform.machine(),
                'processor': platform.processor(),
                'hostname': platform.node(),
                'python_version': platform.python_version(),
                'boot_time': boot_time.strftime('%Y-%m-%d %H:%M:%S'),
                'uptime': f'{hours}sa {mins}dk',
                'label': f'Sistem: {platform.system()} {platform.node()} | Çalışma: {hours}sa {mins}dk'
            }
        except Exception as e:
            return {'os': 'Bilinmiyor', 'os_version': '', 'machine': '', 'processor': '', 'hostname': '', 'python_version': '', 'boot_time': '', 'uptime': '', 'label': f'Sistem: Hata - {e}'}

    def get_processes_by_cpu(self, top_n=5):
        try:
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    info = p.info
                    procs.append({
                        'pid': info['pid'],
                        'name': info['name'],
                        'cpu': info['cpu_percent'] or 0,
                        'memory': info['memory_percent'] or 0
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            procs.sort(key=lambda x: x['cpu'], reverse=True)
            return procs[:top_n]
        except Exception as e:
            return []

    def get_full_report(self):
        cpu = self.get_cpu_usage()
        mem = self.get_memory_info()
        disk = self.get_disk_info()
        bat = self.get_battery_info()
        net = self.get_network_info()
        sys_info = self.get_system_info()

        report_lines = [
            f'Sistem Raporu - {datetime.now().strftime("%d.%m.%Y %H:%M")}',
            f'İşletim Sistemi: {sys_info["os"]} {sys_info["machine"]}',
            f'CPU: %{cpu["percent"]:.1f} ({cpu["cores"]} çekirdek, {cpu["freq_mhz"]:.0f} MHz)',
            f'RAM: %{mem["percent"]:.1f} ({mem["used_gb"]:.1f}/{mem["total_gb"]:.1f} GB)',
            f'Disk: {disk["label"]}',
            f'Batarya: {bat["label"]}',
            f'Ağ: {net["label"]}',
            f'Çalışma Süresi: {sys_info["uptime"]}',
        ]
        return '\n'.join(report_lines)

    def get_status_dict(self):
        return {
            'cpu': self.get_cpu_usage(),
            'memory': self.get_memory_info(),
            'disk': self.get_disk_info(),
            'battery': self.get_battery_info(),
            'network': self.get_network_info(),
            'system': self.get_system_info(),
        }
