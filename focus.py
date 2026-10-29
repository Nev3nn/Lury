from datetime import date
import customtkinter as ctk
from rules import PTS_PER_MIN
from storage import save, TIMER_DEFAULT
from theme import PRIMARY, GOLD, TEAL, RED

SHOP = [("🪑", "Cadeira", 100), ("💡", "Abajur", 120), ("🪴", "Planta", 150),
        ("🖼️", "Quadro", 250), ("📚", "Estante", 400), ("🛏️", "Cama", 500),
        ("🛋️", "Sofá", 600), ("🖥️", "Computador", 800), ("🏆", "Troféu", 1500)]

class FocusTab(ctk.CTkFrame):
    KEY = {"Foco": "focus", "Pausa curta": "short", "Pausa longa": "long"}
    ICON = {"Foco": "🎯", "Pausa curta": "☕", "Pausa longa": "🌴"}

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.running, self.job, self.phase, self.done = app, False, None, "Foco", 0
        L = ctk.CTkFrame(self); L.pack(side="left", fill="y", padx=(0, 8), pady=4, ipadx=14)
        self.phase_lbl = ctk.CTkLabel(L, text="", font=("Segoe UI", 16, "bold")); self.phase_lbl.pack(pady=(14, 0))
        self.clock = ctk.CTkLabel(L, text="25:00", font=("Consolas", 56, "bold"), text_color=GOLD); self.clock.pack(pady=8)
        self.subj = ctk.CTkOptionMenu(L, values=["Geral"]); self.subj.pack(pady=4)
        self.btn = ctk.CTkButton(L, text="▶ Iniciar Estudo", height=40, command=self.toggle, **PRIMARY)
        self.btn.pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(L, text="↺ Reiniciar", fg_color="gray30", command=self.restart).pack(padx=20, fill="x")
        ctk.CTkButton(L, text="⚙ Configurar timer", fg_color="gray30", command=self.settings).pack(padx=20, pady=(6, 0), fill="x")
        self.info = ctk.CTkLabel(L, text=f"+{PTS_PER_MIN} pontos por minuto de foco", text_color="gray70"); self.info.pack(pady=10)
        R = ctk.CTkFrame(self); R.pack(side="left", fill="both", expand=True, pady=4)
        self.title = ctk.CTkLabel(R, font=("Segoe UI", 18, "bold")); self.title.pack(pady=(14, 6))
        self.house = ctk.CTkFrame(R, fg_color="#232940"); self.house.pack(pady=4)
        self.shop = ctk.CTkScrollableFrame(R, label_text="🛒 Loja"); self.shop.pack(fill="both", expand=True, padx=10, pady=8)
        self.reset()

    def cfg(self):
        return {**TIMER_DEFAULT, **self.app.data["timer"]}

    def show(self):
        c = self.cfg(); t = self.elapsed if c["mode"] == "Progressivo" else self.left
        self.clock.configure(text=f"{t // 60:02d}:{t % 60:02d}")
        extra = f" • ciclo {self.done % c['cycles'] + 1}/{c['cycles']}" if c["mode"] == "Regressivo" else " • progressivo"
        self.phase_lbl.configure(text=f"{self.ICON[self.phase]} {self.phase}{extra}")

    def reset(self, *_):
        self.running = False
        if self.job: self.after_cancel(self.job); self.job = None
        c = self.cfg(); self.elapsed = 0
        if c["mode"] == "Progressivo": self.phase = "Foco"
        self.left = c[self.KEY[self.phase]] * 60
        self.btn.configure(text="▶ Iniciar Estudo" if self.phase == "Foco" else "▶ Iniciar Pausa"); self.show()

    def restart(self):
        self.phase, self.done = "Foco", 0; self.reset()

    def toggle(self):
        self.running = not self.running
        if self.job: self.after_cancel(self.job); self.job = None
        self.btn.configure(text="⏸ Pausar" if self.running else "▶ Continuar")
        if self.running: self.job = self.after(1000, self.tick)

    def tick(self):
        self.elapsed += 1
        if self.phase == "Foco" and self.elapsed % 60 == 0: self.award()  # pausas não rendem pontos
        if self.cfg()["mode"] == "Regressivo":
            self.left -= 1
            if self.left <= 0: return self.finish_phase()
        self.show(); self.job = self.after(1000, self.tick)

    def finish_phase(self):
        self.bell()
        if self.phase == "Foco":
            self.done += 1
            self.phase = "Pausa longa" if self.done % self.cfg()["cycles"] == 0 else "Pausa curta"
        else:
            self.phase = "Foco"
        self.reset(); self.info.configure(text=f"🎉 Fase concluída! Próxima: {self.phase}")

    def award(self):
        d = self.app.data
        s = d["sessions"].setdefault(date.today().isoformat(), {"total": 0})
        s["total"] += 1; s[self.subj.get()] = s.get(self.subj.get(), 0) + 1
        d["points"] += PTS_PER_MIN
        self.app.commit()

    def settings(self):
        c = self.cfg(); w = ctk.CTkToplevel(self); w.title("Configurar timer"); w.geometry("380x400")
        w.transient(self.winfo_toplevel()); w.after(150, w.grab_set)
        ents = {}
        for key, text in [("focus", "Foco (min)"), ("short", "Pausa curta (min)"), ("long", "Pausa longa (min)"),
                          ("cycles", "Focos até a pausa longa")]:
            r = ctk.CTkFrame(w, fg_color="transparent"); r.pack(fill="x", padx=24, pady=6)
            ctk.CTkLabel(r, text=text, anchor="w", width=180).pack(side="left")
            e = ctk.CTkEntry(r, width=70); e.insert(0, str(c[key])); e.pack(side="left"); ents[key] = e
        mode = ctk.CTkSegmentedButton(w, values=["Regressivo", "Progressivo"]); mode.set(c["mode"]); mode.pack(pady=12)
        ctk.CTkLabel(w, text="Regressivo: Pomodoro com pausas.\nProgressivo: conta para cima, sem pausas.",
                     text_color="gray70").pack()
        err = ctk.CTkLabel(w, text="", text_color=RED); err.pack(pady=4)

        def ok():
            try: v = {k: int(e.get()) for k, e in ents.items()}
            except ValueError: return err.configure(text="Use números inteiros.")
            if any(not 1 <= x <= 180 for x in v.values()): return err.configure(text="Use valores de 1 a 180.")
            self.app.data["timer"] = {**v, "mode": mode.get()}; save(self.app.data)
            w.destroy(); self.restart()
        ctk.CTkButton(w, text="Salvar", command=ok, **PRIMARY).pack(pady=8)

    def buy(self, name, price):
        d = self.app.data
        if d["points"] >= price and name not in d["items"]:
            d["points"] -= price; d["items"].append(name); self.app.commit()

    def refresh(self):
        d = self.app.data
        self.subj.configure(values=list(d["subjects"]) + ["Geral"])
        for w in self.house.winfo_children() + self.shop.winfo_children(): w.destroy()
        self.title.configure(text=f"🏠 Sua casa — {len(d['items'])}/{len(SHOP)} itens")
        for i, (emo, name, price) in enumerate(SHOP):
            own = name in d["items"]
            ctk.CTkLabel(self.house, text=emo if own else "·", width=84, height=70,
                         font=("Segoe UI Emoji", 34), text_color="white" if own else "gray35"
                         ).grid(row=i // 3, column=i % 3, padx=3, pady=3)
            row = ctk.CTkFrame(self.shop, fg_color="transparent"); row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{emo} {name}", width=140, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{price} pts", text_color=GOLD).pack(side="left", padx=8)
            ctk.CTkButton(row, width=100, text="✔ Comprado" if own else "Comprar",
                          state="disabled" if own or d["points"] < price else "normal",
                          command=lambda n=name, p=price: self.buy(n, p)).pack(side="right")
