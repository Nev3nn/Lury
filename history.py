from datetime import date
from tkinter import messagebox
import customtkinter as ctk
from rules import overall, sub_scores, level
from storage import save
from theme import PRIMARY, GOLD, TEAL, VIOLET, MUTED, EDGE, CARD, CARD2, INK, LV, chip

def spark(parent, sims):
    """Gráfico de linha com a nota geral (0-10) dos últimos simulados."""
    pts, W, H = sims[-12:], 640, 130
    c = ctk.CTkCanvas(parent, width=W, height=H, highlightthickness=0, bg=CARD); c.pack(padx=14, pady=(0, 10))
    for v in (0, 5, 10):
        y = H - 20 - v / 10 * (H - 40)
        c.create_line(30, y, W - 10, y, fill=EDGE); c.create_text(14, y, text=str(v), fill=MUTED, font=("Segoe UI", 8))
    n = len(pts); xs = [30 + (W - 50) * (i / (n - 1) if n > 1 else 0.5) for i in range(n)]
    ys = [H - 20 - overall(s) / 10 * (H - 40) for s in pts]
    if n > 1: c.create_line(*[v for p in zip(xs, ys) for v in p], fill=VIOLET, width=3, smooth=True)
    for x, y, s in zip(xs, ys, pts):
        c.create_oval(x - 5, y - 5, x + 5, y + 5, fill=GOLD, outline="")
        c.create_text(x, y - 14, text=f"{overall(s):.1f}", fill="white", font=("Segoe UI", 9, "bold"))
        c.create_text(x, H - 6, text=f"{s['date'][8:10]}/{s['date'][5:7]}", fill=MUTED, font=("Segoe UI", 8))

def delete(tab, i):
    if messagebox.askyesno("Excluir simulado", "Excluir este simulado do histórico?\nA análise e os reajustes passam a ignorá-lo."):
        del tab.app.data["simulados"][i]; save(tab.app.data); tab.refresh()

def build(tab):
    d = tab.app.data; sims = d["simulados"]
    row = ctk.CTkFrame(tab.body, fg_color="transparent"); row.pack(fill="x", pady=(0, 4))
    ctk.CTkButton(row, text="➕ Registrar simulado", command=tab.register, **PRIMARY).pack(side="left")
    if not sims:
        ctk.CTkLabel(tab.body, text="Nenhum simulado registrado ainda.\nQuando você registrar, todos ficam guardados aqui.", text_color=MUTED).pack(pady=40); return
    sc = [overall(s) for s in sims]
    tab.kpis([("📝", len(sims), "simulados guardados", VIOLET, "{:.0f}"), ("📈", sum(sc) / len(sc), "média geral", GOLD, "{:.1f}"),
              ("🏆", max(sc), "melhor nota", TEAL, "{:.1f}"), ("🕑", sc[-1], "última nota", LV[level(sc[-1])], "{:.1f}")])
    s = tab.section("Evolução das notas (0 a 10)"); spark(s, sims)
    s = tab.section(f"Histórico completo ({len(sims)})")
    for i in range(len(sims) - 1, -1, -1):
        sim = sims[i]; nota = overall(sim)
        card = ctk.CTkFrame(s, fg_color=CARD2); card.pack(fill="x", padx=12, pady=5)
        top = ctk.CTkFrame(card, fg_color="transparent"); top.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(top, text="📝 " + date.fromisoformat(sim["date"]).strftime("%d/%m/%Y"), font=("Segoe UI", 14, "bold")).pack(side="left")
        ctk.CTkButton(top, text="🗑", width=30, fg_color="gray30", command=lambda k=i: delete(tab, k)).pack(side="right")
        ctk.CTkLabel(top, text=f" {nota:.1f}/10 ", fg_color=LV[level(nota)], text_color=INK, corner_radius=9, font=("Segoe UI", 12, "bold")).pack(side="right", padx=8)
        if "hits" in sim: ctk.CTkLabel(top, text=f"{sim['hits']:g}/{sim['scale']:g} acertos", text_color=MUTED).pack(side="right")
        chips = ctk.CTkFrame(card, fg_color="transparent"); chips.pack(fill="x", padx=12, pady=(0, 10))
        for k, v in sub_scores(sim).items():
            chip(chips, f"{k} {v:.1f}", LV[level(v)]).pack(side="left", padx=2)
    ctk.CTkLabel(s, text="", height=4).pack()
