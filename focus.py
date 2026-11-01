import time
from datetime import date
import customtkinter as ctk
from house import ITEMS, TITLES, draw
from rules import PTS_PER_MIN
from storage import save, TIMER_DEFAULT
from theme import PRIMARY, GOLD, TEAL, RED

def fmt_t(sec):
    ms = int(sec * 1000); h, ms = divmod(ms, 3600000); m, ms = divmod(ms, 60000); s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"

class FocusTab(ctk.CTkFrame):
    KEY = {"Foco": "focus", "Pausa curta": "short", "Pausa longa": "long"}
    ICON = {"Foco": "🎯", "Pausa curta": "☕", "Pausa longa": "🌴"}

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.running, self.job, self.phase, self.done = app, False, None, "Foco", 0
        self.base, self.t0, self.paid = 0.0, 0.0, 0
        L = ctk.CTkFrame(self); L.pack(side="left", fill="y", padx=(0, 8), pady=4, ipadx=10)
        self.phase_lbl = ctk.CTkLabel(L, text="", font=("Segoe UI", 15, "bold")); self.phase_lbl.pack(pady=(14, 0))
        self.clock = ctk.CTkLabel(L, text="", font=("Consolas", 30, "bold"), text_color=GOLD); self.clock.pack(pady=10, padx=6)
        self.subj = ctk.CTkOptionMenu(L, values=["Geral"]); self.subj.pack(pady=4)
        self.btn = ctk.CTkButton(L, text="▶ Iniciar Estudo", height=40, command=self.toggle, **PRIMARY)
        self.btn.pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(L, text="↺ Reiniciar", fg_color="gray30", command=self.restart).pack(padx=20, fill="x")
        ctk.CTkButton(L, text="⚙ Configurar timer", fg_color="gray30", command=self.settings).pack(padx=20, pady=(6, 0), fill="x")
        ctk.CTkButton(L, text="🛠 +5000 pts (teste)", fg_color="gray20", command=app.dev_points).pack(padx=20, pady=(6, 0), fill="x")
        self.info = ctk.CTkLabel(L, text=f"+{PTS_PER_MIN} pontos por minuto de foco", text_color="gray70", wraplength=230); self.info.pack(pady=10)
        R = ctk.CTkFrame(self); R.pack(side="left", fill="both", expand=True, pady=4)
        self.title = ctk.CTkLabel(R, font=("Segoe UI", 17, "bold")); self.title.pack(pady=(10, 4))
        self.canvas = ctk.CTkCanvas(R, width=544, height=344, highlightthickness=0, bg="#151a2b"); self.canvas.pack()
        self.shop = ctk.CTkScrollableFrame(R, label_text="🛒 Loja"); self.shop.pack(fill="both", expand=True, padx=10, pady=8)
        self.reset()

    def cfg(self):
        c = {**TIMER_DEFAULT, **self.app.data["timer"]}
        c["mode"] = "Progressivo" if c["mode"] == "Progressivo" else "Pomodoro"  # aceita o nome antigo "Regressivo"
        return c

    def total(self):
        return self.cfg()[self.KEY[self.phase]] * 60

    def elapsed(self):
        return self.base + (time.perf_counter() - self.t0 if self.running else 0)

    def show(self, e):
        c = self.cfg(); pomo = c["mode"] == "Pomodoro"
        self.clock.configure(text=fmt_t(max(0, self.total() - e) if pomo else e))
        extra = f" • ciclo {self.done % c['cycles'] + 1}/{c['cycles']}" if pomo else " • progressivo"
        self.phase_lbl.configure(text=f"{self.ICON[self.phase]} {self.phase}{extra}")

    def stop_job(self):
        if self.job: self.after_cancel(self.job); self.job = None

    def reset(self, *_):
        self.running = False; self.stop_job(); self.base, self.paid = 0.0, 0
        if self.cfg()["mode"] == "Progressivo": self.phase = "Foco"
        self.btn.configure(text="▶ Iniciar Estudo" if self.phase == "Foco" else "▶ Iniciar Pausa"); self.show(0)

    def restart(self):
        self.phase, self.done = "Foco", 0; self.reset()

    def toggle(self):
        if self.running:
            self.base = self.elapsed(); self.running = False; self.stop_job()
            self.btn.configure(text="▶ Continuar")
        else:
            self.t0 = time.perf_counter(); self.running = True
            self.btn.configure(text="⏸ Pausar"); self.tick()

    def tick(self):  # relógio real (perf_counter): preciso ao milissegundo, atualiza a cada ~30 ms
        e = self.elapsed()
        if self.phase == "Foco":
            while self.paid < int(e // 60):
                self.paid += 1; self.award()
        if self.cfg()["mode"] == "Pomodoro" and e >= self.total(): return self.finish_phase()
        self.show(e); self.job = self.after(30, self.tick)

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
        save(d); self.app.update_header(); self.refresh()

    def settings(self):
        c = self.cfg(); w = ctk.CTkToplevel(self); w.title("Configurar timer"); w.geometry("380x360")
        w.transient(self.winfo_toplevel()); w.after(150, w.grab_set)
        ents = {}
        mode = ctk.CTkSegmentedButton(w, values=["Pomodoro", "Progressivo"], command=lambda m: build(m))
        mode.set(c["mode"]); mode.pack(pady=(18, 8))
        box = ctk.CTkFrame(w, fg_color="transparent"); box.pack(fill="x")
        err = ctk.CTkLabel(w, text="", text_color=RED); err.pack(pady=4)

        def build(m):  # progressivo = contagem livre: sem pausas, ciclos ou durações
            for x in box.winfo_children(): x.destroy()
            ents.clear()
            if m == "Progressivo":
                ctk.CTkLabel(box, text="Contagem livre para cima (horas, minutos, segundos e milissegundos), "
                             "sem limite e sem pausas.", wraplength=320, text_color="gray70").pack(pady=24)
                return
            ctk.CTkLabel(box, text="Contagem regressiva com pausas.", text_color="gray70").pack(pady=(0, 6))
            for key, text in [("focus", "Foco (min)"), ("short", "Pausa curta (min)"), ("long", "Pausa longa (min)"),
                              ("cycles", "Focos até a pausa longa")]:
                r = ctk.CTkFrame(box, fg_color="transparent"); r.pack(fill="x", padx=24, pady=6)
                ctk.CTkLabel(r, text=text, anchor="w", width=180).pack(side="left")
                e = ctk.CTkEntry(r, width=80); e.insert(0, str(c[key])); e.pack(side="left"); ents[key] = e

        def ok():
            try: v = {k: int(e.get()) for k, e in ents.items()}
            except ValueError: return err.configure(text="Use números inteiros.")
            if any(x < 1 for x in v.values()): return err.configure(text="Use valores a partir de 1.")
            self.app.data["timer"] = {**c, **v, "mode": mode.get()}; save(self.app.data)
            w.destroy(); self.restart()
        ctk.CTkButton(w, text="Salvar", command=ok, **PRIMARY).pack(pady=8)
        build(c["mode"])

    def buy(self, name, price):
        d = self.app.data
        if d["points"] >= price and name not in d["items"]:
            d["points"] -= price; d["items"].append(name); self.app.commit()

    def refresh(self):
        d = self.app.data; n = len(d["items"])
        self.subj.configure(values=list(d["subjects"]) + ["Geral"])
        self.title.configure(text=f"🏠 {TITLES[min(n // 6, 4)]} — {n}/{len(ITEMS)} itens")
        draw(self.canvas, d["items"])
        for w in self.shop.winfo_children(): w.destroy()
        for name, emo, price, *_ in ITEMS:
            own = name in d["items"]
            row = ctk.CTkFrame(self.shop, fg_color="transparent"); row.pack(fill="x", pady=2)
            ctk.CTkLabel(row, text=f"{emo} {name}", width=170, anchor="w").pack(side="left")
            ctk.CTkLabel(row, text=f"{price} pts", text_color=GOLD).pack(side="left", padx=8)
            ctk.CTkButton(row, width=100, text="✔ Comprado" if own else "Comprar",
                          state="disabled" if own or d["points"] < price else "normal",
                          command=lambda a=name, p=price: self.buy(a, p)).pack(side="right")
