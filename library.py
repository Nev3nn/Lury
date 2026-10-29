import os, re, sys, subprocess, unicodedata
import customtkinter as ctk
from storage import BASE
from theme import PRIMARY, TEAL

FOLDER = os.path.join(BASE, "PDFs")
OLD = os.path.join(BASE, "Aulas")  # nome antigo: migrado automaticamente

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

def slug(name):  # "Matemática" -> "Matematica"
    s = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^\w\- ]", "", s).strip() or "Materia"

def pdfs(path):
    return [(f, os.path.getsize(os.path.join(path, f))) for f in sorted(os.listdir(path)) if f.lower().endswith(".pdf")]

def scan(subjects):
    """Cria PDFs/<Matéria> para cada matéria do cronograma. Retorna ({pasta: matéria}, {pasta: [(arquivo, tamanho)]})."""
    if os.path.isdir(OLD) and not os.path.exists(FOLDER):
        os.rename(OLD, FOLDER)
    os.makedirs(FOLDER, exist_ok=True)
    names = {slug(s): s for s in subjects}
    for k in names:
        os.makedirs(os.path.join(FOLDER, k), exist_ok=True)
    groups = {e: pdfs(os.path.join(FOLDER, e)) for e in sorted(os.listdir(FOLDER)) if os.path.isdir(os.path.join(FOLDER, e))}
    if pdfs(FOLDER):
        groups[""] = pdfs(FOLDER)  # PDFs soltos na raiz = "Outros"
    return names, groups

class LibraryTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.sig, self.filter = app, None, "Todas"
        top = ctk.CTkFrame(self, fg_color="transparent"); top.pack(fill="x")
        self.seg = ctk.CTkSegmentedButton(top, values=["Todas"], command=self.set_filter); self.seg.pack(side="left")
        ctk.CTkButton(top, text="Atualizar", width=90, command=self.refresh).pack(side="right")
        ctk.CTkButton(top, text="📂 Abrir pasta", width=110, fg_color="gray30",
                      command=lambda: open_file(FOLDER)).pack(side="right", padx=6)
        self.grid_f = ctk.CTkScrollableFrame(self); self.grid_f.pack(fill="both", expand=True, pady=8)
        for c in range(3):
            self.grid_f.columnconfigure(c, weight=1, uniform="c")
        self.watch()

    def watch(self):  # monitora a pasta a cada 3 s (e cria pastas de novas matérias)
        if scan(self.app.data["subjects"]) != self.sig:
            self.refresh()
        self.after(3000, self.watch)

    def set_filter(self, v):
        self.filter = v; self.refresh()

    def refresh(self):
        names, groups = self.sig = scan(self.app.data["subjects"])
        label = {k: names.get(k, k or "Outros") for k in groups}
        choices = ["Todas"] + list(dict.fromkeys(label.values()))
        self.seg.configure(values=choices)
        if self.filter not in choices: self.filter = "Todas"
        self.seg.set(self.filter)
        for w in self.grid_f.winfo_children():
            w.destroy()
        items = [(label[k], k, f, sz) for k, fs in groups.items() for f, sz in fs if self.filter in ("Todas", label[k])]
        if not items:
            ctk.CTkLabel(self.grid_f, text="Nenhum PDF aqui ainda.\nColoque arquivos na pasta PDFs\\<matéria>.",
                         text_color="gray70").grid(row=0, column=0, columnspan=3, pady=40)
        for i, (subj, k, f, sz) in enumerate(items):
            card = ctk.CTkFrame(self.grid_f, corner_radius=12)
            card.grid(row=i // 3, column=i % 3, padx=6, pady=6, sticky="nsew")
            ctk.CTkLabel(card, text=subj.upper(), text_color=TEAL, font=("Segoe UI", 11, "bold")).pack(pady=(12, 0))
            ctk.CTkLabel(card, text="📄 " + f, wraplength=210, font=("Segoe UI", 14, "bold")).pack(padx=10, pady=(2, 2))
            ctk.CTkLabel(card, text=fmt(sz), text_color="gray70").pack()
            ctk.CTkButton(card, text="Abrir PDF", command=lambda p=os.path.join(FOLDER, k, f): open_file(p),
                          **PRIMARY).pack(padx=14, pady=12, fill="x")
