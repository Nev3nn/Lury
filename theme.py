"""Identidade visual (dark), componentes reutilizáveis e animações."""
import time
import customtkinter as ctk

GOLD, TEAL, RED, INK = "#f2b84b", "#3fb8a5", "#e5634d", "#14161f"
VIOLET, BG, CARD, CARD2, EDGE, MUTED = "#7c6cf0", "#0d1020", "#171b30", "#1f2440", "#2c3358", "#8d93ab"
PRIMARY = dict(fg_color=GOLD, hover_color="#d9a13a", text_color=INK)
LV = {"crítico": RED, "fraco": "#e8913a", "ok": GOLD, "forte": TEAL}
TAGS = [VIOLET, TEAL, GOLD, RED, "#4a90d9", "#d96fa8", "#6fcf97", "#f2994a"]

def tag_color(name):  # cor estável por matéria / categoria / subcategoria
    return TAGS[sum(map(ord, name)) % len(TAGS)]

def apply():
    """Repinta o tema padrão do CustomTkinter (chamar antes de criar a janela)."""
    T, p = ctk.ThemeManager.theme, (lambda c: [c, c])
    def up(name, **kw): T.setdefault(name, {}).update({k: p(v) if isinstance(v, str) else v for k, v in kw.items()})
    up("CTk", fg_color=BG); up("CTkToplevel", fg_color=BG)
    up("CTkFrame", fg_color=CARD, top_fg_color=CARD2, border_color=EDGE, corner_radius=14)
    up("CTkButton", fg_color=VIOLET, hover_color="#6455d6", corner_radius=10)
    up("CTkProgressBar", fg_color=EDGE, progress_color=TEAL)
    up("CTkSlider", fg_color=EDGE, progress_color=VIOLET, button_color=GOLD, button_hover_color="#d9a13a")
    up("CTkOptionMenu", fg_color=CARD2, button_color=VIOLET, button_hover_color="#6455d6")
    up("CTkSegmentedButton", fg_color=CARD2, selected_color=VIOLET, selected_hover_color="#6455d6",
       unselected_color=CARD2, unselected_hover_color=EDGE)
    up("CTkEntry", fg_color=BG, border_color=EDGE); up("CTkTextbox", fg_color=BG, border_color=EDGE)
    up("CTkCheckBox", fg_color=VIOLET, hover_color="#6455d6", border_color=EDGE)
    up("CTkScrollableFrame", label_fg_color=CARD2)

def header(parent, title, sub=""):
    f = ctk.CTkFrame(parent, fg_color="transparent"); f.pack(fill="x", pady=(0, 8))
    ctk.CTkLabel(f, text=title, font=("Segoe UI", 22, "bold")).pack(side="left", padx=(4, 10))
    if sub: ctk.CTkLabel(f, text=sub, text_color=MUTED).pack(side="left", pady=(6, 0))
    return f

def chip(parent, text, color=VIOLET):  # etiqueta colorida
    return ctk.CTkLabel(parent, text=f" {text} ", fg_color=color, text_color=INK, corner_radius=9, height=22, font=("Segoe UI", 11, "bold"))

def animate(bar, target, ms=650, from_current=False):
    """Preenche a barra com easing suave (cúbico)."""
    s0, t0 = (bar.get() if from_current else 0.0), time.perf_counter()
    def step():
        try:
            k = min(1.0, (time.perf_counter() - t0) * 1000 / ms)
            bar.set(s0 + (target - s0) * (1 - (1 - k) ** 3))
            if k < 1: bar.after(16, step)
        except Exception:
            pass  # widget já destruído
    step()

def count_up(label, to, fmt="{:.1f}", ms=700):
    t0 = time.perf_counter()
    def step():
        try:
            k = min(1.0, (time.perf_counter() - t0) * 1000 / ms)
            label.configure(text=fmt.format(to * (1 - (1 - k) ** 3)))
            if k < 1: label.after(16, step)
        except Exception:
            pass
    step()

def kpi(parent, icon, value, label, color=TEAL, fmt="{:.0f}", text=None):
    f = ctk.CTkFrame(parent, border_width=1)
    ctk.CTkLabel(f, text=icon, font=("Segoe UI Emoji", 22)).pack(pady=(10, 0))
    v = ctk.CTkLabel(f, text=text or "0", font=("Segoe UI", 24, "bold"), text_color=color); v.pack()
    if text is None: count_up(v, value, fmt)
    ctk.CTkLabel(f, text=label, text_color=MUTED, wraplength=150).pack(pady=(0, 10), padx=8)
    return f
