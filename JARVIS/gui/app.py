import customtkinter as ctk
import tkinter as tk
import threading
import queue
import math
import time
from datetime import datetime
from config import COLORS, APP_NAME, APP_VERSION, APP_SUBTITLE, BOOT_MESSAGES


ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('dark-blue')


class ArcReactorWidget(tk.Canvas):
    def __init__(self, parent, size=280, **kwargs):
        super().__init__(parent, width=size, height=size, bg=COLORS['bg_dark'],
                         highlightthickness=0, **kwargs)
        self.size = size
        self.cx = size // 2
        self.cy = size // 2
        self.state = 'idle'
        self.rotation1 = 0
        self.rotation2 = 0
        self.rotation3 = 0
        self.glow = 0.0
        self.glow_dir = 1
        self.speaking_amp = 0.0
        self.particles = []
        for i in range(80):
            self.particles.append({
                'angle': math.radians(i * 4.5),
                'dist': 50 + (i % 5) * 30,
                'speed': 0.005 + (i % 7) * 0.003,
                'size': 1 + (i % 4) * 0.7,
                'brightness': 0.3 + (i % 6) * 0.12,
            })
        self._animate()

    def set_state(self, state):
        self.state = state

    def set_speaking_amplitude(self, amp):
        self.speaking_amp = amp

    def _get_color(self, alpha=1.0):
        state_colors = {
            'idle': (255, 153, 0),
            'listening': (0, 170, 255),
            'thinking': (255, 204, 0),
            'speaking': (0, 255, 136),
            'error': (255, 51, 68),
        }
        r, g, b = state_colors.get(self.state, (255, 153, 0))
        return f'#{int(r*alpha):02x}{int(g*alpha):02x}{int(b*alpha):02x}'

    def _get_rgb(self):
        state_colors = {
            'idle': (255, 153, 0),
            'listening': (0, 170, 255),
            'thinking': (255, 204, 0),
            'speaking': (0, 255, 136),
            'error': (255, 51, 68),
        }
        return state_colors.get(self.state, (255, 153, 0))

    def _animate(self):
        self.rotation1 += 1.2
        self.rotation2 -= 1.8
        self.rotation3 += 0.8
        self.glow += 0.04 * self.glow_dir
        if self.glow >= 1.0:
            self.glow_dir = -1
        elif self.glow <= 0.0:
            self.glow_dir = 1

        if self.state == 'speaking':
            target_glow = 0.7 + self.speaking_amp * 0.3
            self.glow = self.glow + (target_glow - self.glow) * 0.1
        elif self.state == 'thinking':
            self.glow = max(self.glow, 0.6)

        self.draw()
        self.after(20, self._animate)

    def draw(self):
        self.delete('all')
        w = self.size
        h = self.size
        cx = self.cx
        cy = self.cy
        base_r = w * 0.40
        g = max(0.1, self.glow)
        r, gr, b = self._get_rgb()

        for i in range(6, 0, -1):
            off = i * 12 * g
            alpha_hex = format(int(min(255, 30 * g * (7 - i) / 7)), '02x')
            color = f'#{r:02x}{gr:02x}{b:02x}'
            self.create_oval(
                cx - base_r - off, cy - base_r - off,
                cx + base_r + off, cy + base_r + off,
                outline=color, width=0, fill='', stipple='gray25'
            )

        for p in self.particles:
            p['angle'] += p['speed']
            px = cx + math.cos(p['angle']) * p['dist']
            py = cy + math.sin(p['angle']) * p['dist']
            a = p['brightness'] * g
            pr = min(255, int(r * a))
            pgr = min(255, int(gr * a))
            pb = min(255, int(b * a))
            color = f'#{pr:02x}{pgr:02x}{pb:02x}'
            self.create_oval(
                px - p['size'], py - p['size'],
                px + p['size'], py + p['size'],
                fill=color, outline=''
            )

        r3d = int(base_r * 0.85)
        segments = 16
        for i in range(segments):
            angle = math.radians(i * (360 / segments) + self.rotation1)
            x1 = cx + math.cos(angle) * (r3d * 0.6)
            y1 = cy + math.sin(angle) * (r3d * 0.6)
            x2 = cx + math.cos(angle) * (r3d * 0.95)
            y2 = cy + math.sin(angle) * (r3d * 0.95)
            color = f'#{min(255,int(r*g)):02x}{min(255,int(gr*g)):02x}{min(255,int(b*g)):02x}'
            self.create_line(x1, y1, x2, y2, fill=color, width=2, capstyle='round')

        arc_segs = 8
        for i in range(arc_segs):
            start = i * (360 / arc_segs) + self.rotation2
            extent = (360 / arc_segs) * 0.6
            color = f'#{min(255,int(r*g*0.7)):02x}{min(255,int(gr*g*0.7)):02x}{min(255,int(b*g*0.7)):02x}'
            self.create_arc(
                cx - r3d, cy - r3d, cx + r3d, cy + r3d,
                start=start, extent=extent, style='arc',
                outline=color, width=2
            )

        inner_r = int(base_r * 0.65)
        inner_segs = 12
        for i in range(inner_segs):
            start = i * (360 / inner_segs) + self.rotation3
            extent = (360 / inner_segs) * 0.5
            color = f'#{min(255,int(r*g*0.5)):02x}{min(255,int(gr*g*0.5)):02x}{min(255,int(b*g*0.5)):02x}'
            self.create_arc(
                cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
                start=start, extent=extent, style='arc',
                outline=color, width=1
            )

        ring_r = int(base_r * 0.52)
        color = f'#{min(255,int(r*g*0.6)):02x}{min(255,int(gr*g*0.6)):02x}{min(255,int(b*g*0.6)):02x}'
        self.create_oval(
            cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r,
            outline=color, width=2
        )

        tick_r = int(base_r * 0.55)
        for i in range(60):
            angle = math.radians(i * 6)
            length = 6 if i % 5 == 0 else 3
            x1 = cx + math.cos(angle) * tick_r
            y1 = cy + math.sin(angle) * tick_r
            x2 = cx + math.cos(angle) * (tick_r + length)
            y2 = cy + math.sin(angle) * (tick_r + length)
            color = f'#{min(255,int(r*0.3)):02x}{min(255,int(gr*0.3)):02x}{min(255,int(b*0.3)):02x}'
            self.create_line(x1, y1, x2, y2, fill=color, width=1)

        core_r = int(base_r * 0.35)
        core_dark = f'#{min(255,int(r*0.1)):02x}{min(255,int(gr*0.1)):02x}{min(255,int(b*0.1)):02x}'
        self.create_oval(
            cx - core_r, cy - core_r, cx + core_r, cy + core_r,
            fill=core_dark, outline=''
        )

        glow_r = int(base_r * 0.25)
        for i in range(5):
            gr2 = glow_r + i * 4
            alpha = max(10, int(40 * g * (5 - i) / 5))
            gc = f'#{min(255,int(r*alpha/255)):02x}{min(255,int(gr*alpha/255)):02x}{min(255,int(b*alpha/255)):02x}'
            self.create_oval(
                cx - gr2, cy - gr2, cx + gr2, cy + gr2,
                fill='', outline=gc, width=1
            )

        core_bright_r = int(base_r * 0.15)
        color = f'#{min(255,int(r*g)):02x}{min(255,int(gr*g)):02x}{min(255,int(b*g)):02x}'
        self.create_oval(
            cx - core_bright_r, cy - core_bright_r,
            cx + core_bright_r, cy + core_bright_r,
            fill=color, outline=''
        )

        center_r = int(base_r * 0.06)
        self.create_oval(
            cx - center_r, cy - center_r,
            cx + center_r, cy + center_r,
            fill='#ffffff', outline=''
        )


class SplashScreen(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.configure(fg_color='#000000')

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 700, 450
        self.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2}')

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left_frame = ctk.CTkFrame(self, fg_color='transparent')
        left_frame.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        title_label = ctk.CTkLabel(
            left_frame, text=f'{APP_NAME} V{APP_VERSION}',
            font=ctk.CTkFont(family='Consolas', size=18, weight='bold'),
            text_color='#00f0ff'
        )
        title_label.pack(anchor='w', pady=(0, 2))

        sub_label = ctk.CTkLabel(
            left_frame, text=APP_SUBTITLE,
            font=ctk.CTkFont(family='Consolas', size=8),
            text_color='#006680'
        )
        sub_label.pack(anchor='w', pady=(0, 10))

        self.log_text = ctk.CTkTextbox(
            left_frame, font=ctk.CTkFont(family='Consolas', size=9),
            fg_color='#0a0a1a', text_color='#00cc88',
            border_width=1, border_color='#003344',
            height=280
        )
        self.log_text.pack(fill='both', expand=True)

        right_frame = ctk.CTkFrame(self, fg_color='transparent')
        right_frame.grid(row=0, column=1, sticky='nsew', padx=10, pady=10)

        self.reactor = ArcReactorWidget(right_frame, size=300)
        self.reactor.pack(expand=True)
        self.reactor.set_state('idle')

        self.progress = ctk.CTkProgressBar(
            self, height=3, progress_color='#00f0ff',
            fg_color='#0a1a2a'
        )
        self.progress.grid(row=1, column=0, columnspan=2, sticky='ew', padx=20, pady=(0, 10))
        self.progress.set(0)

        self.boot_index = 0
        self.boot_complete = False
        self.after(500, self._run_boot)

    def _run_boot(self):
        if self.boot_index < len(BOOT_MESSAGES):
            msg = BOOT_MESSAGES[self.boot_index]
            self.log_text.insert('end', f'  > {msg}\n')
            self.log_text.see('end')
            progress = (self.boot_index + 1) / len(BOOT_MESSAGES)
            self.progress.set(progress)
            self.boot_index += 1
            delay = 150 + (self.boot_index % 3) * 100
            self.after(delay, self._run_boot)
        else:
            self.boot_complete = True
            self.after(800, self._finish_boot)

    def _finish_boot(self):
        self.destroy()
        self.parent.deiconify()
        self.parent.lift()
        if hasattr(self.parent, 'on_boot_complete'):
            self.parent.on_boot_complete()


class JarvisHUD(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f'{APP_NAME} V{APP_VERSION}')
        self.configure(fg_color=COLORS['bg_dark'])

        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w, h = 1100, 700
        self.geometry(f'{w}x{h}+{(sw-w)//2}+{(sh-h)//2}')
        self.minsize(900, 600)

        self.withdraw()

        self.status = 'idle'
        self.chat_history = []
        self.is_listening = False
        self.is_speaking = False
        self.input_queue = queue.Queue()
        self.output_queue = queue.Queue()

        self._build_ui()
        self.after(100, self._show_splash)

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        left_panel = ctk.CTkFrame(self, fg_color=COLORS['bg_mid'], width=320, corner_radius=0)
        left_panel.grid(row=0, column=0, sticky='nsew')
        left_panel.grid_propagate(False)

        ctk.CTkLabel(
            left_panel, text=APP_NAME,
            font=ctk.CTkFont(family='Orbitron', size=22, weight='bold'),
            text_color=COLORS['accent_orange']
        ).pack(pady=(20, 2))

        ctk.CTkLabel(
            left_panel, text=APP_SUBTITLE,
            font=ctk.CTkFont(family='Consolas', size=8),
            text_color=COLORS['text_dim']
        ).pack(pady=(0, 10))

        self.arc_reactor = ArcReactorWidget(left_panel, size=260)
        self.arc_reactor.pack(pady=10)

        self.status_label = ctk.CTkLabel(
            left_panel, text='BOŞTA',
            font=ctk.CTkFont(family='Consolas', size=12, weight='bold'),
            text_color=COLORS['accent_orange']
        )
        self.status_label.pack(pady=(5, 10))

        ctrl_frame = ctk.CTkFrame(left_panel, fg_color='transparent')
        ctrl_frame.pack(fill='x', padx=15, pady=5)

        ctk.CTkLabel(ctrl_frame, text='SES:', font=ctk.CTkFont(size=10),
                      text_color=COLORS['text_dim']).pack(anchor='w')
        self.voice_var = ctk.StringVar(value='Erkek (Ahmet)')
        ctk.CTkOptionMenu(ctrl_frame, variable=self.voice_var,
                          values=['Erkek (Ahmet)', 'Kadın (Elif)'],
                          font=ctk.CTkFont(size=11),
                          fg_color=COLORS['bg_light'],
                          button_color=COLORS['accent_orange'],
                          width=250).pack(fill='x', pady=2)

        ctk.CTkLabel(ctrl_frame, text='MİK:', font=ctk.CTkFont(size=10),
                      text_color=COLORS['text_dim']).pack(anchor='w', pady=(5, 0))
        self.mic_var = ctk.StringVar(value='Varsayılan')
        self.mic_menu = ctk.CTkOptionMenu(ctrl_frame, variable=self.mic_var,
                                           values=['Varsayılan'],
                                           font=ctk.CTkFont(size=11),
                                           fg_color=COLORS['bg_light'],
                                           button_color=COLORS['accent_orange'],
                                           width=250)
        self.mic_menu.pack(fill='x', pady=2)

        self.mic_btn = ctk.CTkButton(
            left_panel, text='🎤 Mikrofonu Aç',
            font=ctk.CTkFont(size=13, weight='bold'),
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['accent_green'],
            text_color=COLORS['accent_blue'],
            border_width=1, border_color=COLORS['accent_blue'],
            height=45, corner_radius=22,
            command=self._toggle_mic
        )
        self.mic_btn.pack(pady=10, padx=15, fill='x')

        right_panel = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'], corner_radius=0)
        right_panel.grid(row=0, column=1, sticky='nsew')
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(right_panel, fg_color=COLORS['bg_mid'], height=45, corner_radius=0)
        top_bar.grid(row=0, column=0, sticky='ew')
        top_bar.grid_columnconfigure(1, weight=1)

        self.status_dot = ctk.CTkLabel(
            top_bar, text='●', font=ctk.CTkFont(size=16),
            text_color=COLORS['accent_orange']
        )
        self.status_dot.grid(row=0, column=0, padx=10)

        ctk.CTkLabel(
            top_bar, text=APP_NAME,
            font=ctk.CTkFont(family='Orbitron', size=12, weight='bold'),
            text_color=COLORS['text_primary']
        ).grid(row=0, column=1, sticky='w')

        self.top_status = ctk.CTkLabel(
            top_bar, text='Hazır',
            font=ctk.CTkFont(size=10),
            text_color=COLORS['text_dim']
        )
        self.top_status.grid(row=0, column=1, sticky='w', padx=(100, 0))

        self.clock_label = ctk.CTkLabel(
            top_bar, text='',
            font=ctk.CTkFont(family='Consolas', size=12),
            text_color=COLORS['text_dim']
        )
        self.clock_label.grid(row=0, column=2, padx=15)
        self._update_clock()

        self.chat_frame = ctk.CTkScrollableFrame(
            right_panel, fg_color=COLORS['bg_dark'],
            scrollbar_button_color=COLORS['bg_light'],
            scrollbar_button_hover_color=COLORS['accent_orange']
        )
        self.chat_frame.grid(row=1, column=0, sticky='nsew', padx=5, pady=5)
        self.chat_frame.grid_columnconfigure(0, weight=1)

        self.welcome_label = ctk.CTkLabel(
            self.chat_frame,
            text=f'KOMUT BEKLENİYOR\n\nMikrofonu açın veya yazarak başlayın\n\n"Hey Jarvis" ile sesli komut verin',
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_dim'],
            justify='center'
        )
        self.welcome_label.grid(row=0, column=0, pady=100, sticky='nsew')

        input_bar = ctk.CTkFrame(right_panel, fg_color=COLORS['bg_mid'], height=60, corner_radius=0)
        input_bar.grid(row=2, column=0, sticky='ew')
        input_bar.grid_columnconfigure(0, weight=1)

        self.input_entry = ctk.CTkTextbox(
            input_bar, height=40,
            font=ctk.CTkFont(size=13),
            fg_color=COLORS['bg_light'],
            text_color=COLORS['text_primary'],
            border_width=1, border_color=COLORS['border'],
            corner_radius=10
        )
        self.input_entry.grid(row=0, column=0, sticky='ew', padx=(10, 5), pady=10)
        self.input_entry.bind('<Return>', self._on_enter)

        self.send_btn = ctk.CTkButton(
            input_bar, text='Gönder',
            font=ctk.CTkFont(size=12, weight='bold'),
            fg_color=COLORS['accent_orange'],
            hover_color=COLORS['accent_gold'],
            text_color='#000000',
            width=80, height=40, corner_radius=10,
            command=self._send_message
        )
        self.send_btn.grid(row=0, column=1, padx=(0, 10), pady=10)

        info_label = ctk.CTkLabel(
            input_bar,
            text=f'{APP_NAME} v{APP_VERSION} | URC Team | "Hey Jarvis" ile etkinleştirin',
            font=ctk.CTkFont(family='Consolas', size=9),
            text_color=COLORS['text_dim']
        )
        info_label.grid(row=1, column=0, columnspan=2, pady=(0, 5))

    def _update_clock(self):
        now = datetime.now()
        self.clock_label.configure(text=now.strftime('%H:%M:%S'))
        self.after(1000, self._update_clock)

    def _show_splash(self):
        SplashScreen(self)

    def on_boot_complete(self):
        self._add_system_message('Sistem hazır. Komutlarınızı bekliyorum.')

    def _add_system_message(self, text):
        self.welcome_label.destroy() if self.welcome_label.winfo_exists() else None
        frame = ctk.CTkFrame(self.chat_frame, fg_color=COLORS['bg_light'], corner_radius=10)
        frame.grid(row=len(self.chat_frame.winfo_children()), column=0, sticky='ew', pady=4, padx=5)
        ctk.CTkLabel(
            frame, text=f'SİSTEM',
            font=ctk.CTkFont(family='Orbitron', size=9, weight='bold'),
            text_color=COLORS['accent_blue']
        ).pack(anchor='w', padx=10, pady=(8, 0))
        ctk.CTkLabel(
            frame, text=text,
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_primary'],
            wraplength=500, justify='left'
        ).pack(anchor='w', padx=10, pady=(2, 8))
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def _add_user_message(self, text):
        self.welcome_label.destroy() if self.welcome_label.winfo_exists() else None
        frame = ctk.CTkFrame(self.chat_frame, fg_color='#1a2540', corner_radius=10)
        frame.grid(row=len(self.chat_frame.winfo_children()), column=0, sticky='ew', pady=4, padx=5)
        ctk.CTkLabel(
            frame, text='SEN',
            font=ctk.CTkFont(family='Orbitron', size=9, weight='bold'),
            text_color=COLORS['text_dim']
        ).pack(anchor='e', padx=10, pady=(8, 0))
        ctk.CTkLabel(
            frame, text=text,
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_primary'],
            wraplength=500, justify='right'
        ).pack(anchor='e', padx=10, pady=(2, 8))
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def _add_ai_message(self, text):
        self.welcome_label.destroy() if self.welcome_label.winfo_exists() else None
        frame = ctk.CTkFrame(self.chat_frame, fg_color='#1a1510', corner_radius=10)
        frame.grid(row=len(self.chat_frame.winfo_children()), column=0, sticky='ew', pady=4, padx=5)
        ctk.CTkLabel(
            frame, text='J.A.R.V.I.S.',
            font=ctk.CTkFont(family='Orbitron', size=9, weight='bold'),
            text_color=COLORS['accent_orange']
        ).pack(anchor='w', padx=10, pady=(8, 0))
        ctk.CTkLabel(
            frame, text=text,
            font=ctk.CTkFont(size=13),
            text_color=COLORS['text_primary'],
            wraplength=500, justify='left'
        ).pack(anchor='w', padx=10, pady=(2, 8))
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def _add_thinking(self):
        frame = ctk.CTkFrame(self.chat_frame, fg_color='#1a1510', corner_radius=10)
        frame.grid(row=len(self.chat_frame.winfo_children()), column=0, sticky='ew', pady=4, padx=5, name='thinking_frame')
        ctk.CTkLabel(
            frame, text='J.A.R.V.I.S.',
            font=ctk.CTkFont(family='Orbitron', size=9, weight='bold'),
            text_color=COLORS['accent_orange']
        ).pack(anchor='w', padx=10, pady=(8, 0))
        dots = ctk.CTkLabel(
            frame, text='● ● ●',
            font=ctk.CTkFont(size=16),
            text_color=COLORS['accent_orange']
        )
        dots.pack(anchor='w', padx=10, pady=(2, 8))
        self._thinking_dots = dots
        self.chat_frame._parent_canvas.yview_moveto(1.0)

    def _remove_thinking(self):
        try:
            for widget in self.chat_frame.winfo_children():
                if str(widget) == 'thinking_frame' or (hasattr(widget, 'cget') and hasattr(widget, '_name') and widget._name == 'thinking_frame'):
                    widget.destroy()
                    break
        except Exception:
            pass

    def set_state(self, state):
        self.status = state
        state_map = {
            'idle': ('BOŞTA', COLORS['accent_orange']),
            'listening': ('DİNLENİYOR', COLORS['accent_blue']),
            'thinking': ('DÜŞÜNÜYOR', COLORS['accent_gold']),
            'speaking': ('KONUŞUYOR', COLORS['accent_green']),
            'error': ('HATA', COLORS['accent_red']),
        }
        text, color = state_map.get(state, ('BOŞTA', COLORS['accent_orange']))
        self.status_label.configure(text=text, text_color=color)
        self.top_status.configure(text=text)
        self.status_dot.configure(text_color=color)
        self.arc_reactor.set_state(state)

    def set_speaking_amplitude(self, amp):
        self.arc_reactor.set_speaking_amplitude(amp)

    def update_mic_list(self, mics):
        names = [name for _, name in mics] if mics else ['Varsayılan']
        self.mic_menu.configure(values=names)

    def _toggle_mic(self):
        if self.is_listening:
            self.is_listening = False
            self.mic_btn.configure(text='🎤 Mikrofonu Aç', fg_color=COLORS['bg_light'],
                                   text_color=COLORS['accent_blue'])
            self.input_queue.put(('stop_listening', None))
        else:
            self.is_listening = True
            self.mic_btn.configure(text='⏹ Dinlemeyi Durdur', fg_color='#2a1010',
                                   text_color=COLORS['accent_red'])
            self.input_queue.put(('start_listening', None))

    def _on_enter(self, event):
        self._send_message()

    def _send_message(self):
        text = self.input_entry.get('1.0', 'end').strip()
        if not text:
            return
        self.input_entry.delete('1.0', 'end')
        self._add_user_message(text)
        self.input_queue.put(('process_input', text))

    def receive_response(self, text):
        self.after(0, lambda: self._add_ai_message(text))

    def receive_thinking_start(self):
        self.after(0, self._add_thinking)

    def receive_thinking_end(self):
        self.after(0, self._remove_thinking)

    def receive_status(self, state):
        self.after(0, lambda: self.set_state(state))

    def receive_speaking_amp(self, amp):
        self.after(0, lambda: self.set_speaking_amplitude(amp))

    def receive_system_message(self, text):
        self.after(0, lambda: self._add_system_message(text))

    def receive_mic_list(self, mics):
        self.after(0, lambda: self.update_mic_list(mics))
