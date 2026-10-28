from datetime import date
import customtkinter as ctk
from rules import goal_min, studied, week_days, weekly_minutes, propose_adjustment
from storage import save
from theme import PRIMARY, GOLD, TEAL, RED

class StatsTab(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

    def head(self, text):
        ctk.CTkLabel(self, text=text, font=("Segoe UI", 16, "bold"), anchor="w").pack(fill="x", padx=8, pady=(18, 2))

    def bar(self, text, val, goal):
        ctk.CTkLabel(self, text=text, anchor="w").pack(fill="x", padx=10, pady=(6, 0))
        p = ctk.CTkProgressBar(self, progress_color=TEAL if val >= goal else GOLD)
        p.pack(fill="x", padx=10, pady=2); p.set(min(1, val / goal) if goal else 0)

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        d = self.app.data
        if not d["schedule"]:
            ctk.CTkLabel(self, text="Monte seu cronograma na aba Cronograma para ver as métricas.",
                         text_color="gray70").pack(pady=40); return
        g, days = goal_min(d), [x for x in week_days() if x <= date.today()]
        hoje, semana = studied(d, date.today()), sum(studied(d, x) for x in days)
        self.head("Metas")
        self.bar(f"{'✅' if hoje >= g else '⏳'} Hoje: {hoje}/{g} min", hoje, g)
        self.bar(f"{'✅' if semana >= g * 7 else '⏳'} Semana: {semana}/{g * 7} min", semana, g * 7)
        self.head("Matérias da semana")
        for s, m in weekly_minutes(d["subjects"], d["daily_goal_h"]).items():
            done = sum(studied(d, x, s) for x in days)
            self.bar(f"{s}: {done}/{m} min" + ("  ⚠ pendente" if done < m else "  ✅"), done, m)
        self.head("Penalidades do ano")
        year = str(date.today().year)
        lost = sum(e["loss"] for e in d["penalty_log"] if e["date"].startswith(year))
        ctk.CTkLabel(self, text=f"Pontos perdidos em {year}: {lost}  •  dias seguidos sem meta: {d['streak_miss']}",
                     text_color=RED if lost else "gray70", anchor="w").pack(fill="x", padx=10)
        for e in d["penalty_log"][-5:]:
            ctk.CTkLabel(self, text=f"   {e['date']}: -{e['loss']} pts ({e['streak']} dias seguidos)", anchor="w",
                         text_color="gray70").pack(fill="x", padx=10)
        self.head("Registrar simulado (notas de 0 a 10)")
        row = ctk.CTkFrame(self, fg_color="transparent"); row.pack(fill="x", padx=8)
        self.entries = {}
        for s, w in d["subjects"].items():
            if w == 0: continue
            e = ctk.CTkEntry(row, width=90, placeholder_text=s); e.pack(side="left", padx=4); self.entries[s] = e
        ctk.CTkButton(row, text="Registrar", width=90, command=self.register, **PRIMARY).pack(side="left", padx=8)
        self.msg = ctk.CTkLabel(self, text="", text_color=RED, anchor="w"); self.msg.pack(fill="x", padx=10)
        for sim in d["simulados"][-4:]:
            txt = ", ".join(f"{k} {v:g}" for k, v in sim["scores"].items())
            ctk.CTkLabel(self, text=f"📝 {sim['date']}: {txt}", anchor="w", text_color="gray70").pack(fill="x", padx=10)
        falta = 2 - (len(d["simulados"]) - d["last_adjust"])
        ctk.CTkLabel(self, text=f"O reajuste automático acontece a cada 2 simulados (faltam {max(falta, 0)}).",
                     anchor="w", text_color="gray70").pack(fill="x", padx=10, pady=4)

    def register(self):
        d, sc = self.app.data, {}
        for s, e in self.entries.items():
            t = e.get().strip().replace(",", ".")
            if not t: continue
            try: v = float(t)
            except ValueError: return self.msg.configure(text="Use apenas números nas notas.")
            if not 0 <= v <= 10: return self.msg.configure(text="As notas devem estar entre 0 e 10.")
            sc[s] = v
        if not sc: return self.msg.configure(text="Informe ao menos uma nota.")
        d["simulados"].append({"date": date.today().isoformat(), "scores": sc}); save(d)
        if len(d["simulados"]) - d["last_adjust"] >= 2: self.propose()
        else: self.app.refresh()

    def propose(self):
        d = self.app.data
        new, changes, sched = propose_adjustment(d)
        if not changes:
            d["last_adjust"] = len(d["simulados"]); save(d); return self.app.refresh()
        old_m, new_m = weekly_minutes(d["subjects"], d["daily_goal_h"]), weekly_minutes(new, d["daily_goal_h"])
        win = ctk.CTkToplevel(self); win.title("Nova grade de estudos"); win.geometry("520x440")
        win.transient(self.winfo_toplevel()); win.after(150, win.grab_set)
        ctk.CTkLabel(win, text="Seus últimos 2 simulados mudaram a grade", font=("Segoe UI", 17, "bold")).pack(pady=(16, 8))
        box = ctk.CTkScrollableFrame(win); box.pack(fill="both", expand=True, padx=16)
        for s, o, n, avg, dl in changes:
            arrow = "🔺" if n > o else "🔻" if n < o else "➖"
            ctk.CTkLabel(box, anchor="w", justify="left", text=(
                f"{arrow} {s}: dificuldade {o} → {n}\n    média {avg:.1f} ({dl:+.1f} entre os simulados) • "
                f"{old_m.get(s, 0)} → {new_m.get(s, 0)} min/semana")).pack(fill="x", pady=4)

        def close(accept):
            if accept: d.update(subjects=new, schedule=sched)
            d["last_adjust"] = len(d["simulados"]); save(d); win.destroy(); self.app.refresh()
        ctk.CTkLabel(win, text="Aceita a Nova Grade?", font=("Segoe UI", 15, "bold")).pack(pady=(10, 4))
        b = ctk.CTkFrame(win, fg_color="transparent"); b.pack(pady=10)
        ctk.CTkButton(b, text="Aceita a Nova Grade", command=lambda: close(True), **PRIMARY).pack(side="left", padx=6)
        ctk.CTkButton(b, text="Manter a atual", fg_color="gray30", command=lambda: close(False)).pack(side="left", padx=6)
