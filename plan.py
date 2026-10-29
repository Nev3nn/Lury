from datetime import date, timedelta
import customtkinter as ctk
from rules import DAYS, build_schedule, weekly_minutes
from storage import save
from theme import PRIMARY, GOLD, RED

class PlanTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.mode = app, "Hoje"

    def clear(self):
        for w in self.winfo_children(): w.destroy()

    def refresh(self):
        self.clear()
        self.view() if self.app.data["schedule"] else self.wizard()

    # ---------- Assistente (3 perguntas) ----------
    def wizard(self):
        f = ctk.CTkFrame(self); f.pack(pady=30, ipadx=24, ipady=10)
        ctk.CTkLabel(f, text="Vamos montar seu cronograma", font=("Segoe UI", 20, "bold")).pack(pady=(16, 10))
        ctk.CTkLabel(f, text="Quais matérias você vai estudar? (separe por vírgula)").pack()
        self.e_sub = ctk.CTkEntry(f, width=380, placeholder_text="Matemática, Física, Inglês"); self.e_sub.pack(pady=6)
        ctk.CTkLabel(f, text="Quantas horas por dia você quer estudar?").pack()
        self.e_h = ctk.CTkEntry(f, width=120, placeholder_text="2.5"); self.e_h.pack(pady=6)
        ctk.CTkLabel(f, text="Quantas matérias você quer estudar por dia?").pack()
        self.e_n = ctk.CTkEntry(f, width=120, placeholder_text="2"); self.e_n.pack(pady=6)
        self.err = ctk.CTkLabel(f, text="", text_color=RED); self.err.pack()
        ctk.CTkButton(f, text="Próximo", command=self.step2, **PRIMARY).pack(pady=10)

    def step2(self):
        subs = list(dict.fromkeys(s.strip() for s in self.e_sub.get().split(",") if s.strip()))
        try: h = float(self.e_h.get().replace(",", ".")); n = int(self.e_n.get())
        except ValueError: h = n = 0
        if not subs or h <= 0 or n < 1:
            return self.err.configure(text="Informe matérias, horas por dia (> 0) e matérias por dia (>= 1).")
        self.clear()
        f = ctk.CTkScrollableFrame(self, label_text="Dificuldade de cada matéria (1 = fácil, 5 = muito difícil)")
        f.pack(fill="both", expand=True, padx=40, pady=10)
        self.sl = {}
        for s in subs:
            r = ctk.CTkFrame(f, fg_color="transparent"); r.pack(fill="x", pady=6)
            ctk.CTkLabel(r, text=s, width=160, anchor="w").pack(side="left")
            v = ctk.CTkLabel(r, text="3", width=24)
            sl = ctk.CTkSlider(r, from_=1, to=5, number_of_steps=4,
                               command=lambda x, l=v: l.configure(text=str(int(round(x)))))
            sl.set(3); sl.pack(side="left", fill="x", expand=True, padx=8); v.pack(side="left"); self.sl[s] = sl
        self.err = ctk.CTkLabel(self, text="", text_color=RED); self.err.pack()
        ctk.CTkButton(self, text="Gerar cronograma", command=lambda: self.finish(h, n), **PRIMARY).pack(pady=10)

    def finish(self, h, n):
        w = {s: int(round(sl.get())) for s, sl in self.sl.items()}
        n = min(n, len(w)); d = self.app.data
        d.update(subjects=w, daily_goal_h=h, per_day=n, schedule=build_schedule(w, h, n), schedule_date=date.today().isoformat())
        self.app.commit()

    # ---------- Cronograma + To-Do ----------
    def view(self):
        d = self.app.data
        top = ctk.CTkFrame(self, fg_color="transparent"); top.pack(fill="x", pady=(0, 6))
        wm = weekly_minutes(d["subjects"], d["daily_goal_h"])
        ctk.CTkLabel(top, text=f"Meta: {d['daily_goal_h']:g} h/dia  •  {sum(wm.values()) / 60:.1f} h/semana  •  {d['per_day']} matéria(s)/dia",
                     font=("Segoe UI", 15, "bold"), text_color=GOLD).pack(side="left", padx=8)
        ctk.CTkButton(top, text="Reconfigurar", width=110, fg_color="gray30",
                      command=lambda: (self.clear(), self.wizard())).pack(side="right")
        left = ctk.CTkScrollableFrame(self, label_text="Grade semanal")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        for s, m in sorted(wm.items(), key=lambda x: -x[1]):
            ctk.CTkLabel(left, text=f"{s}: {m // 60}h{m % 60:02d} (dificuldade {d['subjects'][s]})",
                         anchor="w").pack(fill="x", padx=6)
        for i, day in enumerate(DAYS):
            hoje = i == date.today().weekday()
            ctk.CTkLabel(left, text=day + (" (hoje)" if hoje else ""), anchor="w",
                         font=("Segoe UI", 14, "bold"), text_color=GOLD if hoje else None).pack(fill="x", padx=6, pady=(12, 0))
            for t in d["schedule"].get(day, []):
                ctk.CTkLabel(left, text=f"   {t['subject']} — {t['minutes']} min", anchor="w").pack(fill="x", padx=6)
        right = ctk.CTkScrollableFrame(self, label_text="To-Do")
        right.pack(side="left", fill="both", expand=True)
        ctk.CTkSegmentedButton(right, values=["Hoje", "Semana"], command=self.set_mode).pack(pady=6)
        self.todo(right)

    def set_mode(self, m):
        self.mode = m; self.refresh()

    def todo(self, parent):
        d, today = self.app.data, date.today()
        days = [today] if self.mode == "Hoje" else [today - timedelta(today.weekday()) + timedelta(i) for i in range(7)]
        for day in days:
            tasks = d["schedule"].get(DAYS[day.weekday()], [])
            if self.mode != "Hoje":
                ctk.CTkLabel(parent, text=f"{DAYS[day.weekday()]} {day:%d/%m}", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(8, 0))
            for t in tasks:
                key = f"{day.isoformat()}|{t['subject']}"
                var = ctk.BooleanVar(value=d["todo"].get(key, False))
                ctk.CTkCheckBox(parent, text=f"{t['subject']} — {t['minutes']} min", variable=var,
                                command=lambda k=key, v=var: self.check(k, v)).pack(anchor="w", pady=3)

    def check(self, key, var):
        self.app.data["todo"][key] = var.get(); save(self.app.data)
