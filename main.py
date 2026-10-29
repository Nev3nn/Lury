import customtkinter as ctk
from storage import load, save
from datetime import date
from tkinter import messagebox
from rules import apply_penalties, reminder_due, DEV_BONUS
from simulado import WeightsDialog
from library import LibraryTab
from focus import FocusTab
from plan import PlanTab
from cards import CardsTab
from stats import StatsTab
from theme import GOLD

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lyra Study"); self.geometry("1020x700"); self.minsize(940, 620)
        self.data = load(); apply_penalties(self.data)
        if self.data['schedule'] and not self.data['schedule_date']: self.data['schedule_date'] = date.today().isoformat()
        save(self.data)
        self.views = {}
        self.header = ctk.CTkLabel(self, font=("Segoe UI", 20, "bold"), text_color=GOLD, anchor="w")
        self.header.pack(fill="x", padx=20, pady=(12, 0))
        self.tabs = ctk.CTkTabview(self, command=self.refresh); self.tabs.pack(fill="both", expand=True, padx=12, pady=8)
        for name, cls in [("📚 PDFs", LibraryTab), ("⏱️ Foco e Loja", FocusTab),
                          ("🗓️ Cronograma", PlanTab), ("🧠 Revisão", CardsTab), ("📊 Desempenho", StatsTab)]:
            v = cls(self.tabs.add(name), self); v.pack(fill="both", expand=True); self.views[name] = v
        for k in "Pp": self.bind(f"<Control-Shift-{k}>", self.dev_points)  # atalho de teste: +5000 pontos
        self.refresh(); self.after(800, self.remind)

    def update_header(self):
        self.header.configure(text=f"Lyra Study   ⭐ {self.data['points']} pontos")

    def dev_points(self, *_):
        self.data["points"] += DEV_BONUS; self.commit()

    def remind(self):
        d, today = self.data, date.today().isoformat()
        if reminder_due(d) and d["reminded"] != today:
            d["reminded"] = today; save(d)
            if messagebox.askyesno("Lembrete", "Faz mais de 1 mês sem registrar um simulado.\nRecomendamos revisar manualmente os graus de dificuldade das matérias.\n\nRevisar agora?"):
                WeightsDialog(self, self)

    def refresh(self):
        self.update_header()
        v = self.views.get(self.tabs.get())
        if v: v.refresh()

    def commit(self):
        save(self.data); self.refresh()

if __name__ == "__main__":
    App().mainloop()
