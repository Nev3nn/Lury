import time
from datetime import date
from tkinter import messagebox
import customtkinter as ctk
import theme
from storage import load, save
from rules import apply_penalties, reminder_due, DEV_BONUS
from simulado import WeightsDialog
from library import LibraryTab
from focus import FocusTab
from plan import PlanTab
from cards import CardsTab
from stats import StatsTab
from theme import GOLD, VIOLET, CARD, CARD2, MUTED, animate

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
theme.apply()  # paleta escura + cantos arredondados em todos os widgets

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Lyra Study"); self.geometry("1100x760"); self.minsize(980, 660)
        self.data = load(); apply_penalties(self.data)
        if self.data['schedule'] and not self.data['schedule_date']: self.data['schedule_date'] = date.today().isoformat()
        save(self.data)
        self.views, self.shown, self._tok = {}, 0, 0
        bar = ctk.CTkFrame(self, corner_radius=16); bar.pack(fill="x", padx=14, pady=(12, 0))
        ctk.CTkLabel(bar, text="✦ Lyra Study", font=("Segoe UI", 22, "bold"), text_color=GOLD).pack(side="left", padx=16, pady=10)
        self.pts = ctk.CTkLabel(bar, text="⭐ 0 pts", font=("Segoe UI", 16, "bold"), text_color=GOLD, fg_color=CARD2, corner_radius=12, height=34, width=130)
        self.pts.pack(side="right", padx=14)
        self.lv_bar = ctk.CTkProgressBar(bar, width=150, height=10, progress_color=VIOLET); self.lv_bar.set(0); self.lv_bar.pack(side="right")
        self.lv_lbl = ctk.CTkLabel(bar, text="Nv 1", text_color=MUTED, font=("Segoe UI", 13, "bold")); self.lv_lbl.pack(side="right", padx=8)
        self.tabs = ctk.CTkTabview(self, command=self.on_tab, corner_radius=16, segmented_button_selected_color=VIOLET,
                                   segmented_button_selected_hover_color="#6455d6", segmented_button_unselected_color=CARD2)
        self.tabs.pack(fill="both", expand=True, padx=14, pady=8)
        for name, cls in [("📚 PDFs", LibraryTab), ("⏱️ Foco e Loja", FocusTab), ("🗓️ Cronograma", PlanTab),
                          ("🧠 Revisão", CardsTab), ("📊 Desempenho", StatsTab)]:
            v = cls(self.tabs.add(name), self); v.pack(fill="both", expand=True); self.views[name] = v
        for k in "Pp": self.bind(f"<Control-Shift-{k}>", self.dev_points)  # atalho de teste: +5000 pontos
        self.refresh(); self.after(800, self.remind)

    def on_tab(self):
        self.refresh(); self.wipe()

    def wipe(self):
        """Transição entre abas: uma cortina sobe revelando o conteúdo."""
        tab = self.tabs.tab(self.tabs.get()); fg = tab.cget("fg_color")
        ov = ctk.CTkFrame(tab, corner_radius=0, fg_color=CARD if fg == "transparent" else fg)
        ov.place(x=0, y=0, relwidth=1, relheight=1); t0 = time.perf_counter()
        def step():
            try:
                k = min(1.0, (time.perf_counter() - t0) / 0.28)
                if k >= 1: ov.destroy(); return
                ov.place_configure(relheight=1 - k * k * (3 - 2 * k)); self.after(14, step)
            except Exception:
                pass
        step()

    def update_header(self):
        d = self.data; lvl, rem = divmod(sum(v.get("total", 0) for v in d["sessions"].values()), 300)  # 1 nível = 5 h de foco
        self.lv_lbl.configure(text=f"Nv {lvl + 1}"); animate(self.lv_bar, rem / 300, 500, True)
        self._tok += 1; tok, frm, to, t0 = self._tok, self.shown, d["points"], time.perf_counter()
        def step():  # contador de pontos animado
            k = min(1.0, (time.perf_counter() - t0) / 0.45)
            self.shown = int(frm + (to - frm) * (1 - (1 - k) ** 3)); self.pts.configure(text=f"⭐ {self.shown} pts")
            if k < 1 and tok == self._tok: self.after(16, step)
        step()

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
