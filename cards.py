import uuid
from copy import copy
from datetime import date
import customtkinter as ctk
from rules import schedule_card
from storage import save
from theme import PRIMARY, GOLD, TEAL, RED

GRADES = [("Errei", RED), ("Difícil", "#c98a3a"), ("Bom", TEAL), ("Fácil", "#4a90d9")]

class CardsTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.mode, self.filter, self.queue, self.show_ans, self.last_sub = app, "Estudar", "Todas", [], False, None
        self.seg = ctk.CTkSegmentedButton(self, values=["Estudar", "Gerenciar"], command=self.set_mode)
        self.seg.pack(anchor="w")
        self.body = ctk.CTkFrame(self, fg_color="transparent"); self.body.pack(fill="both", expand=True, pady=8)

    def set_mode(self, m):
        self.mode = m; self.refresh()

    def refresh(self):
        self.seg.set(self.mode)
        today = date.today().isoformat()
        cards = [c for c in self.app.data["cards"] if c["due"] <= today and self.filter in ("Todas", c["subject"])]
        self.queue = [c["id"] for c in sorted(cards, key=lambda c: c["due"])]
        self.show_ans = False
        self.render()

    def render(self):
        for w in self.body.winfo_children(): w.destroy()
        self.study() if self.mode == "Estudar" else self.manage()

    def get(self, cid):
        return next(c for c in self.app.data["cards"] if c["id"] == cid)

    def subjects(self):
        d = self.app.data
        return sorted({*d["subjects"], *(c["subject"] for c in d["cards"])})

    # ---------- Estudar ----------
    def study(self):
        om = ctk.CTkOptionMenu(self.body, values=["Todas"] + self.subjects(), command=self.set_filter)
        om.set(self.filter); om.pack(anchor="e")
        if not self.queue:
            txt = "🎉 Tudo revisado por hoje!" if self.app.data["cards"] else "Você ainda não tem cartões.\nCrie o primeiro na aba Gerenciar."
            ctk.CTkLabel(self.body, text=txt, font=("Segoe UI", 18), text_color="gray70").pack(expand=True); return
        c = self.get(self.queue[0])
        ctk.CTkLabel(self.body, text=f"{c['subject']}  •  {len(self.queue)} para revisar", text_color=GOLD).pack()
        card = ctk.CTkFrame(self.body, corner_radius=16); card.pack(fill="both", expand=True, padx=40, pady=10)
        ctk.CTkLabel(card, text=c["q"], wraplength=560, font=("Segoe UI", 20, "bold")).pack(expand=True, pady=(30, 10))
        if not self.show_ans:
            ctk.CTkButton(self.body, text="Mostrar resposta", height=42, command=self.reveal, **PRIMARY).pack(pady=10); return
        ctk.CTkLabel(card, text=c["a"], wraplength=560, font=("Segoe UI", 17), text_color=TEAL).pack(expand=True, pady=(0, 30))
        row = ctk.CTkFrame(self.body, fg_color="transparent"); row.pack(pady=8)
        for g, (name, col) in enumerate(GRADES):
            t = copy(c); schedule_card(t, g)
            when = "hoje" if t["interval"] == 0 else f"{t['interval']} d"
            ctk.CTkButton(row, text=f"{name}\n{when}", fg_color=col, width=110, height=52,
                          command=lambda g=g: self.grade(g)).pack(side="left", padx=5)

    def set_filter(self, v):
        self.filter = v; self.refresh()

    def reveal(self):
        self.show_ans = True; self.render()

    def grade(self, g):
        cid = self.queue.pop(0); schedule_card(self.get(cid), g)
        if g == 0: self.queue.append(cid)  # volta para o fim da fila desta sessão
        save(self.app.data); self.show_ans = False; self.render()

    # ---------- Criar / Gerenciar ----------
    def manage(self):
        d = self.app.data; subs = list(d["subjects"]) or ["Geral"]
        f = ctk.CTkFrame(self.body); f.pack(fill="x")
        self.sub = ctk.CTkOptionMenu(f, values=subs); self.sub.pack(anchor="w", padx=10, pady=(10, 4))
        if self.last_sub in subs: self.sub.set(self.last_sub)
        ctk.CTkLabel(f, text="Pergunta (frente)", anchor="w").pack(fill="x", padx=10)
        self.q = ctk.CTkTextbox(f, height=60); self.q.pack(fill="x", padx=10, pady=(0, 6))
        ctk.CTkLabel(f, text="Resposta (verso)", anchor="w").pack(fill="x", padx=10)
        self.a = ctk.CTkTextbox(f, height=60); self.a.pack(fill="x", padx=10, pady=(0, 6))
        r = ctk.CTkFrame(f, fg_color="transparent"); r.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(r, text="Adicionar cartão", command=self.add, **PRIMARY).pack(side="left")
        self.msg = ctk.CTkLabel(r, text="", text_color=RED); self.msg.pack(side="left", padx=10)
        lst = ctk.CTkScrollableFrame(self.body, label_text=f"Seus cartões ({len(d['cards'])})")
        lst.pack(fill="both", expand=True, pady=8)
        for c in sorted(d["cards"], key=lambda c: (c["subject"], c["due"])):
            row = ctk.CTkFrame(lst, fg_color="transparent"); row.pack(fill="x")
            ctk.CTkButton(row, text="🗑", width=32, fg_color="gray30", command=lambda i=c["id"]: self.delete(i)).pack(side="right")
            ctk.CTkLabel(row, anchor="w", text=f"[{c['subject']}] {c['q'][:70]}  •  próxima: {c['due']}").pack(side="left", fill="x")

    def add(self):
        q, a = self.q.get("1.0", "end").strip(), self.a.get("1.0", "end").strip()
        if not q or not a: return self.msg.configure(text="Preencha pergunta e resposta.")
        self.last_sub = self.sub.get()
        self.app.data["cards"].append({"id": uuid.uuid4().hex[:8], "subject": self.last_sub, "q": q, "a": a,
                                       "due": date.today().isoformat(), "interval": 0, "ease": 2.5, "reps": 0})
        save(self.app.data); self.render()

    def delete(self, cid):
        self.app.data["cards"] = [c for c in self.app.data["cards"] if c["id"] != cid]
        save(self.app.data); self.render()
