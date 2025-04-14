import threading
import math

try:
    import customtkinter as ctk
    USE_CUSTOM = True
except ImportError:
    import tkinter as tk
    from tkinter import ttk
    USE_CUSTOM = False

# NOTE: True per-pixel transparency is not supported in most Linux Tkinter builds.
# This implementation uses a highly semi-transparent dark background for a "barely there" glassy effect.

class SleekUI:
    def __init__(self):
        if USE_CUSTOM:
            self.root = ctk.CTk()
        else:
            self.root = tk.Tk()
        self.root.title("")
        self.root.geometry("340x180+800+350")
        self.root.resizable(False, False)
        self.root.overrideredirect(True)  # Frameless
        self.root.attributes("-topmost", True)
        # Glassy effect: highly semi-transparent dark background
        self.root.attributes("-alpha", 0.35)
        self.root.configure(bg="#181c20")
        self.root.withdraw()  # Start hidden

        # Subtle border for glassy effect
        if not USE_CUSTOM:
            self.root.configure(highlightthickness=2, highlightbackground="#3defff")

        self._build_ui()
        self.is_visible = False

        # Animation
        self.animating = False
        self.phase = 0

    def _build_ui(self):
        # Canvas for DNA animation
        if USE_CUSTOM:
            self.canvas = ctk.CTkCanvas(self.root, width=320, height=140, bg="#181c20", highlightthickness=0)
        else:
            self.canvas = tk.Canvas(self.root, width=320, height=140, bg="#181c20", highlightthickness=0)
        self.canvas.place(x=10, y=20)

    def run(self):
        self.root.mainloop()

    def show(self):
        def _show():
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.is_visible = True
            if not self.animating:
                self.animating = True
                self._animate_dna()
        self.root.after(0, _show)

    def hide(self):
        def _hide():
            self.animating = False
            self.root.withdraw()
            self.is_visible = False
        self.root.after(0, _hide)

    def update_status(self, text):
        pass  # No status text in this minimal design

    def _animate_dna(self):
        if not self.animating:
            return
        self.canvas.delete("dna")
        w, h = 320, 140
        cx, cy = w // 2, h // 2
        amp = 38
        freq = 2.2
        dot_radius = 6
        color1 = "#00eaff"
        color2 = "#00bfff"
        # Draw two intertwining sine waves (dots)
        for i in range(32):
            t = (i / 31) * (2 * math.pi * freq) + self.phase
            y = cy + math.sin(t) * amp
            x = 30 + i * (w - 60) / 31
            # First strand
            self.canvas.create_oval(
                x-dot_radius, y-dot_radius, x+dot_radius, y+dot_radius,
                fill=color1, outline="", tags="dna"
            )
            # Second strand (phase shifted)
            y2 = cy + math.sin(t + math.pi) * amp
            self.canvas.create_oval(
                x-dot_radius, y2-dot_radius, x+dot_radius, y2+dot_radius,
                fill=color2, outline="", tags="dna"
            )
        # Draw connecting lines (optional, for helix effect)
        for i in range(0, 32, 3):
            t = (i / 31) * (2 * math.pi * freq) + self.phase
            y1 = cy + math.sin(t) * amp
            y2 = cy + math.sin(t + math.pi) * amp
            x = 30 + i * (w - 60) / 31
            self.canvas.create_line(
                x, y1, x, y2, fill="#3defff", width=2, tags="dna"
            )
        self.phase += 0.09
        self.root.after(32, self._animate_dna)

sleek_ui = SleekUI()