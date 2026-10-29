import customtkinter as ctk
from storage import load, save
from rules import apply_penalties
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
        self.title("Lyra Study"); self.geometry("1020x700"); self.minsize(840, 580)
        self.data = load(); apply_penalties(self.data); save(self.data)
        self.views = {}
        self.header = ctk.CTkLabel(self, font=("Segoe UI", 20, "bold"), text_color=GOLD, anchor="w")
        self.header.pack(fill="x", padx=20, pady=(12, 0))
        self.tabs = ctk.CTkTabview(self, command=self.refresh); self.tabs.pack(fill="both", expand=True, padx=12, pady=8)
        for name, cls in [("📚 PDFs", LibraryTab), ("⏱️ Foco e Loja", FocusTab),
                          ("🗓️ Cronograma", PlanTab), ("🧠 Revisão", CardsTab), ("📊 Desempenho", StatsTab)]:
            v = cls(self.tabs.add(name), self); v.pack(fill="both", expand=True); self.views[name] = v
        self.refresh()

    def refresh(self):
        self.header.configure(text=f"Lyra Study   ⭐ {self.data['points']} pontos")
        v = self.views.get(self.tabs.get())
        if v: v.refresh()

    def commit(self):
        save(self.data); self.refresh()

if __name__ == "__main__":
    App().mainloop()
