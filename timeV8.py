import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageEnhance
import os
import time
import threading
import fitz  # PyMuPDF
import sys
import platform

# เช็คระบบปฏิบัติการ
IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import winsound
    import ctypes
    mci = ctypes.windll.winmm
else:
    mci = None

def resource_path(relative_path):
    """ ค้นหาที่อยู่ไฟล์ที่ฝังอยู่ในตัวแอป (.exe หรือ .app) """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AnimatedMinimalistTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Timer Ultra V8 (Mac/Win)")
        self.root.geometry("1200x850")
        self.root.configure(bg="#000000")

        self.color_bg = "#000000"
        self.color_sidebar = "#111111"
        self.color_accent = "#f1c40f"
        # ตำแหน่งไฟล์เสียงที่ฝังมาในแอป
        self.audio_file = resource_path("mp3")

        self.is_running = False
        self.slides = []
        self.current_idx = 0
        self.remaining_seconds = 0

        # --- Layout ---
        self.sidebar = tk.Frame(root, width=180, bg=self.color_sidebar, padx=15, pady=40)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.main_view = tk.Canvas(root, bg=self.color_bg, highlightthickness=0)
        self.main_view.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        font_name = "Arial Black" if not IS_WINDOWS else "Segoe UI Black"
        tk.Label(self.sidebar, text="TIMER", fg=self.color_accent, bg=self.color_sidebar, font=(font_name, 18)).pack(pady=(0,20))

        # Input Time
        e_cfg = {"bg": "#222222", "fg": "white", "relief": "flat", "font": (font_name, 20), "justify": "center", "insertbackground": "white"}
        t_frame = tk.Frame(self.sidebar, bg=self.color_sidebar)
        t_frame.pack()
        self.entry_min = tk.Entry(t_frame, width=2, **e_cfg)
        self.entry_min.insert(0, "01")
        self.entry_min.pack(side=tk.LEFT)
        tk.Label(t_frame, text=":", fg="white", bg=self.color_sidebar, font=("Arial", 20, "bold")).pack(side=tk.LEFT, padx=2)
        self.entry_sec = tk.Entry(t_frame, width=2, **e_cfg)
        self.entry_sec.insert(0, "30")
        self.entry_sec.pack(side=tk.LEFT)

        self.create_round_button("📂 IMAGES", self.load_folder)
        self.create_round_button("📄 PDF FILE", self.load_pdf)

        # --- Navigation Buttons (< >) ---
        nav_frame = tk.Frame(self.sidebar, bg=self.color_sidebar)
        nav_frame.pack(pady=10)
        btn_nav_cfg = {"bg": "#333333", "fg": "white", "font": (font_name, 12), "relief": "flat", "width": 4, "cursor": "hand2"}
        tk.Button(nav_frame, text="<", command=self.prev_slide, **btn_nav_cfg).pack(side=tk.LEFT, padx=5)
        tk.Button(nav_frame, text=">", command=self.next_slide, **btn_nav_cfg).pack(side=tk.LEFT, padx=5)

        self.lbl_display = tk.Label(self.sidebar, text="00:00", font=(font_name, 36), fg=self.color_accent, bg=self.color_sidebar)
        self.lbl_display.pack(pady=20)
        
        self.lbl_status = tk.Label(self.sidebar, text="READY", fg="#555555", bg=self.color_sidebar, font=("Arial Bold", 9))
        self.lbl_status.pack()

        self.btn_start = tk.Button(self.sidebar, text="START", command=self.start_timer_thread, 
                                  bg=self.color_accent, fg="black", font=(font_name, 14), 
                                  relief="flat", width=12, height=2, cursor="hand2")
        self.btn_start.pack(side=tk.BOTTOM, pady=20)

        self.image_on_canvas = self.main_view.create_image(0, 0, anchor=tk.CENTER)
        self.main_view.bind("<Configure>", self.on_resize)

    def create_round_button(self, text, command):
        c = tk.Canvas(self.sidebar, width=150, height=45, bg=self.color_sidebar, highlightthickness=0, cursor="hand2")
        c.pack(pady=10)
        r = c.create_rectangle(5, 5, 145, 40, fill="white", outline="")
        t = c.create_text(75, 22, text=text, fill="black", font=("Arial Bold", 10))
        c.bind("<Button-1>", lambda e: command())

    def prev_slide(self):
        if self.slides:
            self.current_idx = (self.current_idx - 1) % len(self.slides)
            self.show_slide(self.current_idx, animate=False)

    def next_slide(self):
        if self.slides:
            self.current_idx = (self.current_idx + 1) % len(self.slides)
            self.show_slide(self.current_idx, animate=False)

    def play_custom_sound(self):
        def sound():
            if IS_WINDOWS:
                if os.path.exists(self.audio_file):
                    mci.mciSendStringW(f'open "{self.audio_file}" type mpegvideo alias s', None, 0, 0)
                    mci.mciSendStringW('play s', None, 0, 0)
                    time.sleep(2); mci.mciSendStringW('stop s', None, 0, 0); mci.mciSendStringW('close s', None, 0, 0)
                else:
                    for _ in range(5): winsound.Beep(1000, 200)
            else:
                if os.path.exists(self.audio_file):
                    # -t 2 คือเล่นแค่ 2 วินาทีบน Mac
                    os.system(f'afplay -t 2 "{self.audio_file}" &')
                else:
                    os.system('afplay /System/Library/Sounds/Glass.aiff &')
        threading.Thread(target=sound, daemon=True).start()

    def show_slide(self, index, animate=True):
        if 0 <= index < len(self.slides):
            self.current_idx = index
            cw, ch = self.main_view.winfo_width(), self.main_view.winfo_height()
            if cw < 100: cw, ch = 1000, 800
            img = self.slides[index].copy()
            img.thumbnail((cw-60, ch-60), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.main_view.itemconfig(self.image_on_canvas, image=self.photo)
            self.main_view.coords(self.image_on_canvas, cw//2, ch//2)
            self.lbl_status.config(text=f"PAGE {index+1} / {len(self.slides)}")

    def on_resize(self, event):
        if self.slides: self.show_slide(self.current_idx, animate=False)

    def load_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.slides = []
            doc = fitz.open(path)
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                self.slides.append(Image.frombytes("RGB", [pix.width, pix.height], pix.samples))
            doc.close(); self.show_slide(0)

    def load_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.slides = []
            files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            files.sort()
            for f in files: self.slides.append(Image.open(f))
            if self.slides: self.show_slide(0)

    def start_timer_thread(self):
        if not self.slides: return
        self.is_running = not self.is_running
        if self.is_running: threading.Thread(target=self.run_timer, daemon=True).start()

    def run_timer(self):
        try: total_sec = int(self.entry_min.get()) * 60 + int(self.entry_sec.get())
        except: return
        self.btn_start.config(text="STOP")
        for i in range(len(self.slides)):
            if not self.is_running: break
            self.root.after(0, self.show_slide, i)
            self.remaining_seconds = total_sec
            while self.remaining_seconds >= 0 and self.is_running:
                m, s = divmod(self.remaining_seconds, 60)
                self.lbl_display.config(text=f"{m:02d}:{s:02d}")
                self.root.update(); time.sleep(1); self.remaining_seconds -= 1
            if self.is_running: self.play_custom_sound()
        self.is_running = False
        self.btn_start.config(text="START")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnimatedMinimalistTimer(root)
    root.mainloop()
