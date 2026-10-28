from datetime import date
import customtkinter as ctk
from rules import PTS_PER_MIN
from theme import PRIMARY, GOLD, TEAL

SHOP = [("🪑", "Cadeira", 100), ("💡", "Abajur", 120), ("🪴", "Planta", 150),
        ("🖼️", "Quadro", 250), ("📚", "Estante", 400), ("🛏️", "Cama", 500),
        ("🛋️", "Sofá", 600), ("🖥️", "Computador", 800), ("🏆", "Troféu", 1500)]

class FocusTab(ctk.CTkFrame):
    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app, self.running, self.job = app, False, None
        L = ctk.CTkFrame(self); L.pack(side="left", fill="y", padx=(0, 8), pady=4, ipadx=14)
        ctk.CTkLabel(L, text="Foco", font=("Segoe UI", 18, "bold")).pack(pady=(14, 0))
        self.clock = ctk.CTkLabel(L, text="25:00", font=("Consolas", 56, "bold"), text_color=GOLD); self.clock.pack(pady=8)
        self.dur = ctk.CTkOptionMenu(L, values=["15", "25", "50"], command=self.reset); self.dur.set("25"); self.dur.pack(pady=4)
        self.subj = ctk.CTkOptionMenu(L, values=["Geral"]); self.subj.pack(pady=4)
        self.btn = ctk.CTkButton(L, text="▶ Iniciar Estudo", height=40, command=self.toggle, **PRIMARY)
        self.btn.pack(pady=10, padx=20, fill="x")
        ctk.CTkButton(L, text="↺ Reiniciar", fg_color="gray30", command=self.reset).pack(padx=20, fill="x")
        self.info = ctk.CTkLabel(L, text=f"+{PTS_PER_MIN} pontos por minuto", text_color="gray70"); self.info.pack(pady=10)
        R = ctk.CTkFrame(self); R.pack(side="left", fill="both", expand=True, pady=4)
        self.title = ctk.CTkLabel(R, font=("Segoe UI", 18, "bold")); self.title.pack(pady=(14, 6))
        self.house = ctk.CTkFrame(R, fg_color="#232940"); self.house.pack(pady=4)
        self.shop = ctk.CTkScrollableFrame(R, label_text="🛒 Loja"); self.shop.pack(fill="both", expand=True, padx=10, pady=8)
        self.reset()

    def show(self):
        self.clock.configure(text=f"{self.left // 60:02d}:{self.left % 60:02d}")

    def reset(self, *_):
        self.running = False
        if self.job: self.after_cancel(self.job); self.job = None
        self.left, self.elapsed = int(self.dur.get()) * 60, 0
        self.btn.configure(text="▶ Iniciar Estudo"); self.show()

    def toggle(self):
        self.running = not self.running
        if self.job: self.after_cancel(self.job); self.job = None
        self.btn.configure(text="⏸ Pausar" if self.running else "▶ Continuar")
        if self.running: self.tick()

    def tick(self):
        self.left -= 1; self.elapsed += 1
        if self.elapsed % 60 == 0: self.award()
        self.show()
        if self.left <= 0:
            self.bell(); self.reset(); self.info.configure(text="🎉 Sessão concluída!"); return
        self.job = self.after(1000, self.tick)

    def award(self):
        d = self.app.data
        s = d["sessions"].setdefault(date.today().isoformat(), {"total": 0})
        s["total"] += 1; s[self.subj.get()] = s.get(self.subj.get(), 0) + 1
        d["points"] += PTS_PER_MIN
        self.app.commit()

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
