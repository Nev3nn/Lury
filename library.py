import os, re, sys, shutil, subprocess, unicodedata
from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
from storage import BASE, save
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

def scan(subjects, skip=()):
    """Cria PDFs/<Matéria> (exceto as removidas pelo usuário). Retorna ({pasta: matéria}, {pasta: [(arquivo, tamanho)]})."""
    if os.path.isdir(OLD) and not os.path.exists(FOLDER):
        os.rename(OLD, FOLDER)
    os.makedirs(FOLDER, exist_ok=True)
    names = {slug(s): s for s in subjects}
    for k in names:
        if k not in skip:
            os.makedirs(os.path.join(FOLDER, k), exist_ok=True)
    groups = {e: pdfs(os.path.join(FOLDER, e)) for e in sorted(os.listdir(FOLDER))
              if os.path.isdir(os.path.join(FOLDER, e)) and not e.startswith("_")}
    if pdfs(FOLDER):
        groups[""] = pdfs(FOLDER)  # PDFs soltos na raiz = "Outros"
    return names, groups

class LibraryTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.sig, self.filter, self.labels, self.keys = app, None, "Todas", {}, []
        top = ctk.CTkFrame(self, fg_color="transparent"); top.pack(fill="x")
        self.count = ctk.CTkLabel(top, text="", text_color=TEAL); self.count.pack(side="left", padx=8)
        for text, cmd, kw in [("🗑 Pasta", self.remove_folder, dict(fg_color="gray30")), ("➕ Pasta", self.add_folder, PRIMARY),
                              ("📂 Abrir", lambda: open_file(FOLDER), dict(fg_color="gray30")), ("Atualizar", self.refresh, {})]:
            ctk.CTkButton(top, text=text, width=90, command=cmd, **kw).pack(side="right", padx=3)
        self.seg = ctk.CTkSegmentedButton(self, values=["Todas"], command=self.set_filter); self.seg.pack(anchor="w", pady=6)
        self.grid_f = ctk.CTkScrollableFrame(self); self.grid_f.pack(fill="both", expand=True, pady=(0, 8))
        for c in range(3):
            self.grid_f.columnconfigure(c, weight=1, uniform="c")
        self.watch()

    def scan(self):
        return scan(self.app.data["subjects"], self.app.data["skip_folders"])

    def watch(self):  # monitora a pasta a cada 3 s (e cria pastas de novas matérias)
        if self.scan() != self.sig:
            self.refresh()
        self.after(3000, self.watch)

    def set_filter(self, v):
        self.filter = v; self.refresh()

    # ---------- pastas ----------
    def add_folder(self):
        n = ctk.CTkInputDialog(text="Nome da nova pasta:", title="Adicionar pasta").get_input()
        if not n or not n.strip(): return
        k, d = slug(n), self.app.data
        os.makedirs(os.path.join(FOLDER, k), exist_ok=True)
        d["skip_folders"] = [x for x in d["skip_folders"] if x != k]; save(d)
        self.filter = self.scan()[0].get(k, k); self.refresh()

    def remove_folder(self):
        key = next((k for k, lab in self.labels.items() if lab == self.filter), None)
        if not key:
            return messagebox.showinfo("Remover pasta", "Escolha uma pasta no filtro acima e clique em Remover de novo.")
        if not messagebox.askyesno("Remover pasta", f"Remover a pasta '{self.filter}' ({len(self.sig[1][key])} PDF(s))?\n\n"
                                   "Ela será movida para PDFs\\_Removidas, sem apagar seus arquivos."):
            return
        trash = os.path.join(FOLDER, "_Removidas"); os.makedirs(trash, exist_ok=True)
        dest = os.path.join(trash, key)
        if os.path.exists(dest): dest += datetime.now().strftime("_%Y%m%d%H%M%S")
        shutil.move(os.path.join(FOLDER, key), dest)
        d = self.app.data
        if key in self.sig[0] and key not in d["skip_folders"]: d["skip_folders"].append(key)  # pasta de matéria não volta sozinha
        save(d); self.filter = "Todas"; self.refresh()

    # ---------- estudado ----------
    def toggle(self, key, var, card):
        done = self.app.data["pdf_done"]
        if var.get() and key not in done: done.append(key)
        if not var.get() and key in done: done.remove(key)
        card.configure(border_color=TEAL if var.get() else "gray25")
        save(self.app.data); self.update_count()

    def update_count(self):
        done = self.app.data["pdf_done"]
        self.count.configure(text=f"✅ {sum(k in done for k in self.keys)}/{len(self.keys)} estudados")

    def refresh(self):
        names, groups = self.sig = self.scan()
        self.labels = {k: names.get(k, k or "Outros") for k in groups}
        choices = ["Todas"] + list(dict.fromkeys(self.labels.values()))
        self.seg.configure(values=choices)
        if self.filter not in choices: self.filter = "Todas"
        self.seg.set(self.filter)
        for w in self.grid_f.winfo_children():
            w.destroy()
        items = [(self.labels[k], k, f, sz) for k, fs in groups.items() for f, sz in fs if self.filter in ("Todas", self.labels[k])]
        self.keys = [f"{k}/{f}" for _, k, f, _ in items]
        if not items:
            ctk.CTkLabel(self.grid_f, text="Nenhum PDF aqui ainda.\nColoque arquivos na pasta PDFs\\<matéria>.",
                         text_color="gray70").grid(row=0, column=0, columnspan=3, pady=40)
        done = self.app.data["pdf_done"]
        for i, (subj, k, f, sz) in enumerate(items):
            key = f"{k}/{f}"; on = key in done
            card = ctk.CTkFrame(self.grid_f, corner_radius=12, border_width=2, border_color=TEAL if on else "gray25")
            card.grid(row=i // 3, column=i % 3, padx=6, pady=6, sticky="nsew")
            ctk.CTkLabel(card, text=subj.upper(), text_color=TEAL, font=("Segoe UI", 11, "bold")).pack(pady=(12, 0))
            ctk.CTkLabel(card, text="📄 " + f, wraplength=210, font=("Segoe UI", 14, "bold")).pack(padx=10, pady=(2, 2))
            ctk.CTkLabel(card, text=fmt(sz), text_color="gray70").pack()
            var = ctk.BooleanVar(value=on)
            ctk.CTkCheckBox(card, text="Estudado", variable=var,
                            command=lambda a=key, v=var, c=card: self.toggle(a, v, c)).pack(pady=(8, 0))
            ctk.CTkButton(card, text="Abrir PDF", command=lambda p=os.path.join(FOLDER, k, f): open_file(p),
                          **PRIMARY).pack(padx=14, pady=12, fill="x")
        self.update_count()
