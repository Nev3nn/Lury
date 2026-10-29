from datetime import date
import customtkinter as ctk
from rules import (goal_min, studied, week_days, weekly_minutes, analyze, level, overall, sub_scores,
                   propose_adjustment, reminder_due)
from simulado import SimuladoDialog, WeightsDialog
from storage import save
from theme import PRIMARY, GOLD, TEAL, RED

LV = {"crítico": RED, "fraco": "#e8913a", "ok": GOLD, "forte": TEAL}

class StatsTab(ctk.CTkScrollableFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app

    def head(self, text):
        ctk.CTkLabel(self, text=text, font=("Segoe UI", 16, "bold"), anchor="w").pack(fill="x", padx=8, pady=(18, 2))

    def bar(self, text, val, goal, color=None):
        ctk.CTkLabel(self, text=text, anchor="w").pack(fill="x", padx=10, pady=(6, 0))
        p = ctk.CTkProgressBar(self, progress_color=color or (TEAL if val >= goal else GOLD))
        p.pack(fill="x", padx=10, pady=2); p.set(min(1, val / goal) if goal else 0)

    def refresh(self):
        for w in self.winfo_children(): w.destroy()
        d = self.app.data
        if not d["schedule"]:
            ctk.CTkLabel(self, text="Monte seu cronograma na aba Cronograma para ver as métricas.",
                         text_color="gray70").pack(pady=40); return
        if reminder_due(d):
            b = ctk.CTkFrame(self, fg_color="#4a3a1a"); b.pack(fill="x", padx=8, pady=6)
            ctk.CTkLabel(b, text="⏰ Faz mais de 1 mês sem simulado. Recomendamos revisar manualmente os graus de dificuldade.",
                         wraplength=560, justify="left").pack(side="left", padx=10, pady=8)
            ctk.CTkButton(b, text="Revisar agora", width=110, command=lambda: WeightsDialog(self, self.app), **PRIMARY).pack(side="right", padx=10)
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
        self.head("Simulados e análise de desempenho (escala 0 a 10)")
        row = ctk.CTkFrame(self, fg_color="transparent"); row.pack(fill="x", padx=8)
        ctk.CTkButton(row, text="➕ Registrar simulado", command=lambda: SimuladoDialog(self, self.app, self.after_register), **PRIMARY).pack(side="left")
        ctk.CTkButton(row, text="🔧 Revisar dificuldades", fg_color="gray30", command=lambda: WeightsDialog(self, self.app)).pack(side="left", padx=8)
        an = analyze(d)
        if not an:
            ctk.CTkLabel(self, text="Registre um simulado para ver a análise.", text_color="gray70", anchor="w").pack(fill="x", padx=10, pady=8)
        for r in an:
            lv = level(r["avg"]); arrow = "🔺" if r["trend"] > 0.5 else "🔻" if r["trend"] < -0.5 else "➖"
            self.bar(f"{r['subject']}: {r['avg']:.1f}/10  •  {lv}  {arrow}", r["avg"], 10, LV[lv])
        if an:
            weak = [r["subject"] for r in an if r["avg"] < 6]
            ctk.CTkLabel(self, text="🎯 Pontos fracos: " + (", ".join(weak) if weak else "nenhum, ótimo!"),
                         anchor="w", font=("Segoe UI", 14, "bold")).pack(fill="x", padx=10, pady=8)
        for sim in d["simulados"][-4:]:
            txt = ", ".join(f"{k} {v:.1f}" for k, v in sub_scores(sim).items())
            ctk.CTkLabel(self, text=f"📝 {sim['date']}: geral {overall(sim):.1f}/10  •  {txt}", anchor="w",
                         text_color="gray70", wraplength=760, justify="left").pack(fill="x", padx=10)

    def after_register(self):
        new, changes, sched = propose_adjustment(self.app.data)
        self.propose(new, changes, sched) if changes else self.app.refresh()

    def propose(self, new, changes, sched):
        d = self.app.data
        old_m, new_m = weekly_minutes(d["subjects"], d["daily_goal_h"]), weekly_minutes(new, d["daily_goal_h"])
        weak = [r["subject"] for r in analyze(d) if r["avg"] < 6]
        win = ctk.CTkToplevel(self); win.title("Análise do simulado"); win.geometry("540x500")
        win.transient(self.winfo_toplevel()); win.after(150, win.grab_set)
        ctk.CTkLabel(win, text="Análise do simulado", font=("Segoe UI", 17, "bold")).pack(pady=(16, 4))
        ctk.CTkLabel(win, text="🎯 Pontos fracos: " + (", ".join(weak) or "nenhum"), wraplength=480).pack()
        box = ctk.CTkScrollableFrame(win); box.pack(fill="both", expand=True, padx=16, pady=8)
        for s, o, n, avg, dl in changes:
            ctk.CTkLabel(box, anchor="w", justify="left", text=(
                f"{'🔺' if n > o else '🔻'} {s}: dificuldade {o} → {n}\n    nota média {avg:.1f}/10 ({dl:+.1f}) • "
                f"{old_m.get(s, 0)} → {new_m.get(s, 0)} min/semana")).pack(fill="x", pady=4)

        def close(accept):
            if accept: d.update(subjects=new, schedule=sched)
            save(d); win.destroy(); self.app.refresh()
        ctk.CTkLabel(win, text="Aceita a Nova Grade?", font=("Segoe UI", 15, "bold")).pack(pady=(4, 4))
        b = ctk.CTkFrame(win, fg_color="transparent"); b.pack(pady=10)
        ctk.CTkButton(b, text="Aceita a Nova Grade", command=lambda: close(True), **PRIMARY).pack(side="left", padx=6)
        ctk.CTkButton(b, text="Manter a atual", fg_color="gray30", command=lambda: close(False)).pack(side="left", padx=6)
