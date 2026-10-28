import os, sys, subprocess
import customtkinter as ctk
from storage import BASE
from theme import PRIMARY

FOLDER = os.path.join(BASE, "Aulas")

def open_file(path):
    if sys.platform.startswith("win"):
        os.startfile(path)
    else:
        subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", path])

def fmt(n):
    for u in ("B", "KB", "MB"):
        if n < 1024:
            return f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} GB"

def scan():
    os.makedirs(FOLDER, exist_ok=True)
    return [(f, os.path.getsize(os.path.join(FOLDER, f)))
            for f in sorted(os.listdir(FOLDER)) if f.lower().endswith(".pdf")]

class LibraryTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        top = ctk.CTkFrame(self, fg_color="transparent"); top.pack(fill="x")
        ctk.CTkLabel(top, text=f"📂 {FOLDER}", anchor="w", text_color="gray70").pack(side="left", padx=8)
        ctk.CTkButton(top, text="Atualizar", width=90, command=self.refresh).pack(side="right")
        self.grid_f = ctk.CTkScrollableFrame(self); self.grid_f.pack(fill="both", expand=True, pady=8)
        for c in range(3):
            self.grid_f.columnconfigure(c, weight=1, uniform="c")
        self.sig = None
        self.watch()

    def watch(self):  # monitora a pasta a cada 3 s
        if scan() != self.sig:
            self.refresh()
        self.after(3000, self.watch)

    def refresh(self):
        files = scan(); self.sig = files
        for w in self.grid_f.winfo_children():
            w.destroy()
        if not files:
            ctk.CTkLabel(self.grid_f, text="Nenhum PDF por aqui ainda.\nColoque arquivos na pasta Aulas.",
                         text_color="gray70").grid(row=0, column=0, columnspan=3, pady=40)
        for i, (name, size) in enumerate(files):
            card = ctk.CTkFrame(self.grid_f, corner_radius=12)
            card.grid(row=i // 3, column=i % 3, padx=6, pady=6, sticky="nsew")
            ctk.CTkLabel(card, text="📄 " + name, wraplength=210, font=("Segoe UI", 14, "bold")).pack(padx=10, pady=(14, 2))
            ctk.CTkLabel(card, text=fmt(size), text_color="gray70").pack()
            ctk.CTkButton(card, text="Abrir PDF", command=lambda n=name: open_file(os.path.join(FOLDER, n)),
                          **PRIMARY).pack(padx=14, pady=12, fill="x")
