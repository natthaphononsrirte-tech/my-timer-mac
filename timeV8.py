import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk, ImageEnhance
import os
import time
import winsound
import threading
import fitz  # PyMuPDF
import sys
import ctypes

# สำหรับเรียกใช้ mciSendString ใน Windows เพื่อเล่นไฟล์ MP3
mci = ctypes.windll.winmm

def resource_path(relative_path):
    """ ค้นหาไฟล์สำรองเมื่อรันเป็น .exe """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class AnimatedMinimalistTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Minimalist Ultra V8")
        self.root.geometry("1200x850")
        self.root.configure(bg="#000000")

        # Color Settings
        self.color_bg = "#000000"
        self.color_sidebar = "#111111"
        self.color_accent = "#f1c40f" # Yellow
        self.color_btn = "#ffffff"
        self.color_text = "#ffffff"

        # Audio file path
        self.audio_file = resource_path("mp3")

        # State
        self.is_running = False
        self.slides = []
        self.current_idx = 0
        self.remaining_seconds = 0
        self.total_seconds = 0

        # --- Layout ---
        self.sidebar = tk.Frame(root, width=180, bg=self.color_sidebar, padx=15, pady=40)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.main_view = tk.Canvas(root, bg=self.color_bg, highlightthickness=0)
        self.main_view.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # --- Sidebar Widgets ---
        tk.Label(self.sidebar, text="TIMER", fg=self.color_accent, bg=self.color_sidebar, font=("Segoe UI Black", 18)).pack(pady=(0,20))

        # Time Entry Area
        e_cfg = {"bg": "#222222", "fg": "white", "relief": "flat", "font": ("Segoe UI Black", 20), "justify": "center", "insertbackground": "white"}
        t_frame = tk.Frame(self.sidebar, bg=self.color_sidebar)
        t_frame.pack()
        self.entry_min = tk.Entry(t_frame, width=2, **e_cfg)
        self.entry_min.insert(0, "01")
        self.entry_min.pack(side=tk.LEFT)
        tk.Label(t_frame, text=":", fg="white", bg=self.color_sidebar, font=("Arial", 20, "bold")).pack(side=tk.LEFT, padx=2)
        self.entry_sec = tk.Entry(t_frame, width=2, **e_cfg)
        self.entry_sec.insert(0, "30")
        self.entry_sec.pack(side=tk.LEFT)

        # Rounded Buttons
        self.create_round_button("📂 IMAGES", self.load_folder)
        self.create_round_button("📄 PDF FILE", self.load_pdf)

        # Timer Big Display
        self.lbl_display = tk.Label(self.sidebar, text="00:00", font=("Segoe UI Black", 36), fg=self.color_accent, bg=self.color_sidebar)
        self.lbl_display.pack(pady=40)
        
        self.lbl_status = tk.Label(self.sidebar, text="READY", fg="#555555", bg=self.color_sidebar, font=("Segoe UI Bold", 9))
        self.lbl_status.pack()

        # Start Button
        self.btn_start = tk.Button(self.sidebar, text="START", command=self.start_timer_thread, 
                                  bg=self.color_accent, fg="black", font=("Segoe UI Black", 14), 
                                  relief="flat", width=12, height=2, cursor="hand2", activebackground="#d4ac0d")
        self.btn_start.pack(side=tk.BOTTOM, pady=20)

        # Slide Image reference
        self.image_on_canvas = self.main_view.create_image(0, 0, anchor=tk.CENTER)
        self.main_view.bind("<Configure>", self.on_resize)

    def create_round_button(self, text, command):
        c = tk.Canvas(self.sidebar, width=150, height=45, bg=self.color_sidebar, highlightthickness=0, cursor="hand2")
        c.pack(pady=10)
        r = self.draw_rounded_rect(c, 5, 5, 145, 40, 18, fill="white")
        t = c.create_text(75, 22, text=text, fill="black", font=("Segoe UI Bold", 10))
        
        def on_release(e):
            c.move(r, 2, 2); c.move(t, 2, 2)
            self.root.after(100, lambda: (c.move(r, -2, -2), c.move(t, -2, -2), command()))
            
        c.bind("<Button-1>", on_release)
        c.bind("<Enter>", lambda e: c.itemconfig(r, fill="#dddddd"))
        c.bind("<Leave>", lambda e: c.itemconfig(r, fill="white"))

    def draw_rounded_rect(self, canvas, x1, y1, x2, y2, r, **kwargs):
        pts = [x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1]
        return canvas.create_polygon(pts, **kwargs, smooth=True)

    def play_custom_sound(self):
        # เล่นไฟล์เสียงที่ผู้ใช้เลือก ยาว 2 วินาที
        def sound():
            if os.path.exists(self.audio_file):
                path = self.audio_file
                # ใช้ MCI เพื่อเล่นไฟล์ (รองรับ MP3)
                mci.mciSendStringW(f'open "{path}" type mpegvideo alias timer_sound', None, 0, 0)
                mci.mciSendStringW('play timer_sound', None, 0, 0)
                time.sleep(2) # เล่น 2 วินาที
                mci.mciSendStringW('stop timer_sound', None, 0, 0)
                mci.mciSendStringW('close timer_sound', None, 0, 0)
            else:
                # ถ้าไม่พบไฟล์เสียง ให้กริ๊งสำรอง
                for _ in range(40):
                    winsound.Beep(1500, 40)
                    time.sleep(0.01)

        threading.Thread(target=sound, daemon=True).start()

    def on_resize(self, event):
        if self.slides:
            self.show_slide(self.current_idx, animate=False)

    def show_slide(self, index, animate=True):
        if 0 <= index < len(self.slides):
            self.current_idx = index
            cw = self.main_view.winfo_width()
            ch = self.main_view.winfo_height()
            if cw < 100: cw, ch = 1000, 800

            base_img = self.slides[index].copy()
            base_img.thumbnail((cw-60, ch-60), Image.Resampling.LANCZOS)
            
            if animate:
                threading.Thread(target=self.subtle_fade, args=(base_img, cw, ch), daemon=True).start()
            else:
                self.render_image(base_img, cw, ch)

    def subtle_fade(self, target_img, cw, ch):
        for alpha in [0.75, 0.85, 0.95, 1.0]:
            enhancer = ImageEnhance.Brightness(target_img)
            temp = enhancer.enhance(alpha)
            self.root.after(0, self.render_image, temp, cw, ch)
            time.sleep(0.04)

    def render_image(self, img, cw, ch):
        self.photo = ImageTk.PhotoImage(img)
        self.main_view.itemconfig(self.image_on_canvas, image=self.photo)
        self.main_view.coords(self.image_on_canvas, cw//2, ch//2)

    def load_pdf(self):
        path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if path:
            self.slides = []
            try:
                doc = fitz.open(path)
                for page in doc:
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    self.slides.append(img)
                doc.close()
                self.show_slide(0)
            except Exception as e: messagebox.showerror("Error", str(e))

    def load_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.slides = []
            valid = ('.png', '.jpg', '.jpeg', '.gif', '.bmp')
            try:
                files = [os.path.join(path, f) for f in os.listdir(path) if f.lower().endswith(valid)]
                files.sort()
                for f in files: self.slides.append(Image.open(f))
                if self.slides: self.show_slide(0)
            except Exception as e: messagebox.showerror("Error", str(e))

    def start_timer_thread(self):
        if not self.slides:
            messagebox.showinfo("INFO", "LOAD FILES FIRST")
            return
        if not self.is_running:
            self.is_running = True
            threading.Thread(target=self.run_timer, daemon=True).start()
        else:
            self.is_running = False

    def run_timer(self):
        try:
            total_sec = int(self.entry_min.get()) * 60 + int(self.entry_sec.get())
        except: return
        self.btn_start.config(text="STOP", bg="white")
        for i in range(len(self.slides)):
            if not self.is_running: break
            self.root.after(0, self.show_slide, i)
            self.remaining_seconds = total_sec
            while self.remaining_seconds >= 0:
                if not self.is_running: break
                m, s = divmod(self.remaining_seconds, 60)
                self.lbl_display.config(text=f"{m:02d}:{s:02d}")
                self.lbl_status.config(text=f"PAGE {i+1} / {len(self.slides)}")
                self.root.update()
                time.sleep(1)
                self.remaining_seconds -= 1
            if not self.is_running: break
            self.play_custom_sound()
        self.is_running = False
        self.btn_start.config(text="START", bg=self.color_accent)
        self.lbl_display.config(text="00:00")

if __name__ == "__main__":
    root = tk.Tk()
    app = AnimatedMinimalistTimer(root)
    root.mainloop()
