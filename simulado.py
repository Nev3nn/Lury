from datetime import date
import customtkinter as ctk
from rules import build_schedule
from storage import save
from theme import PRIMARY, RED

def num(e):
    try: return float(e.get().strip().replace(",", "."))
    except ValueError: return None

class SimuladoDialog(ctk.CTkToplevel):
    """Passo 1: escala, total de acertos e matérias. Passo 2: acertos (e questões) de cada matéria."""
    def __init__(self, master, app, on_done):
        super().__init__(master); self.title("Registrar simulado"); self.geometry("520x620")
        self.transient(master.winfo_toplevel()); self.after(150, self.grab_set)
        self.app, self.on_done, self.new, self.vars = app, on_done, [], {}
        self.step1()

    def clear(self):
        for w in self.winfo_children(): w.destroy()

    def check(self, n, on=False):
        v = self.vars.setdefault(n, ctk.BooleanVar(value=on))
        ctk.CTkCheckBox(self.box, text=n, variable=v).pack(anchor="w", pady=3)

    def step1(self):
        self.clear()
        ctk.CTkLabel(self, text="Dados da prova", font=("Segoe UI", 18, "bold")).pack(pady=(16, 8))
        r = ctk.CTkFrame(self, fg_color="transparent"); r.pack()
        self.e_scale = ctk.CTkEntry(r, width=210, placeholder_text="Escala total (ex.: 10, 20, 90)"); self.e_scale.grid(row=0, column=0, padx=6)
        self.e_hits = ctk.CTkEntry(r, width=150, placeholder_text="Total de acertos"); self.e_hits.grid(row=0, column=1, padx=6)
        ctk.CTkLabel(self, text="Quais matérias caíram neste simulado?").pack(pady=(14, 2))
        self.box = ctk.CTkScrollableFrame(self, height=200); self.box.pack(fill="x", padx=24)
        for n in self.app.data["subjects"]: self.check(n)
        r2 = ctk.CTkFrame(self, fg_color="transparent"); r2.pack(pady=8)
        self.e_new = ctk.CTkEntry(r2, width=240, placeholder_text="Matéria que não está na lista"); self.e_new.pack(side="left")
        ctk.CTkButton(r2, text="➕ Adicionar", width=100, command=self.add_new).pack(side="left", padx=6)
        self.err = ctk.CTkLabel(self, text="", text_color=RED); self.err.pack()
        ctk.CTkButton(self, text="Continuar", command=self.step2, **PRIMARY).pack(pady=8)

    def add_new(self):
        n = self.e_new.get().strip()
        if not n: return
        if n.lower() in (x.lower() for x in [*self.app.data["subjects"], *self.new]):
            return self.err.configure(text="Essa matéria já está na lista.")
        self.new.append(n); self.check(n, True); self.e_new.delete(0, "end"); self.err.configure(text="")

    def step2(self):
        scale, hits = num(self.e_scale), num(self.e_hits)
        sel = [n for n, v in self.vars.items() if v.get()]
        if not scale or scale <= 0 or hits is None or not 0 <= hits <= scale:
            return self.err.configure(text="Informe a escala (> 0) e acertos entre 0 e a escala.")
        if not sel: return self.err.configure(text="Selecione ao menos uma matéria.")
        self.scale, self.hits = scale, hits
        self.clear()
        ctk.CTkLabel(self, text="Acertos por matéria", font=("Segoe UI", 18, "bold")).pack(pady=(16, 2))
        ctk.CTkLabel(self, text="Ajuste o nº de questões de cada matéria, se precisar.", text_color="gray70").pack()
        box = ctk.CTkScrollableFrame(self); box.pack(fill="both", expand=True, padx=24, pady=8)
        self.rows = {}
        for n in sel:
            r = ctk.CTkFrame(box, fg_color="transparent"); r.pack(fill="x", pady=5)
            ctk.CTkLabel(r, text=n, width=140, anchor="w").pack(side="left")
            a = ctk.CTkEntry(r, width=70, placeholder_text="acertos"); a.pack(side="left")
            ctk.CTkLabel(r, text=" de ").pack(side="left")
            t = ctk.CTkEntry(r, width=70); t.insert(0, str(max(1, round(scale / len(sel))))); t.pack(side="left")
            self.rows[n] = (a, t)
        self.err = ctk.CTkLabel(self, text="", text_color=RED); self.err.pack()
        ctk.CTkButton(self, text="Salvar simulado", command=self.save_sim, **PRIMARY).pack(pady=8)

    def save_sim(self):
        res = {}
        for n, (a, t) in self.rows.items():
            h, tot = num(a), num(t)
            if h is None or not tot or tot <= 0 or not 0 <= h <= tot:
                return self.err.configure(text=f"Confira {n}: acertos entre 0 e o total de questões.")
            res[n] = {"hits": h, "total": tot, "score": round(h / tot * 10, 2)}
        d, added = self.app.data, False
        for n in res:
            if n not in d["subjects"]: d["subjects"][n] = 3; added = True  # matéria nova entra com dificuldade 3
        if added: d["schedule"] = build_schedule(d["subjects"], d["daily_goal_h"], d["per_day"])
        d["simulados"].append({"date": date.today().isoformat(), "scale": self.scale, "hits": self.hits,
                               "score10": round(self.hits / self.scale * 10, 2), "subjects": res})
        save(d); self.destroy(); self.on_done()

class WeightsDialog(ctk.CTkToplevel):
    """Revisão manual dos graus de dificuldade (1 a 5)."""
    def __init__(self, master, app):
        super().__init__(master); self.title("Graus de dificuldade"); self.geometry("460x460")
        self.transient(master.winfo_toplevel()); self.after(150, self.grab_set)
        ctk.CTkLabel(self, text="Dificuldade (1 = fácil, 5 = muito difícil)", font=("Segoe UI", 15, "bold")).pack(pady=12)
        box = ctk.CTkScrollableFrame(self); box.pack(fill="both", expand=True, padx=20)
        self.sl = {}
        for s, w in app.data["subjects"].items():
            r = ctk.CTkFrame(box, fg_color="transparent"); r.pack(fill="x", pady=6)
            ctk.CTkLabel(r, text=s, width=130, anchor="w").pack(side="left")
            v = ctk.CTkLabel(r, text=str(max(1, min(5, int(w)))), width=24)
            sl = ctk.CTkSlider(r, from_=1, to=5, number_of_steps=4, command=lambda x, l=v: l.configure(text=str(int(round(x)))))
            sl.set(max(1, min(5, int(w)))); sl.pack(side="left", fill="x", expand=True, padx=8); v.pack(side="left"); self.sl[s] = sl

        def ok():
            d = app.data
            d["subjects"] = {s: int(round(x.get())) for s, x in self.sl.items()}
            d["schedule"] = build_schedule(d["subjects"], d["daily_goal_h"], d["per_day"])
            d["schedule_date"] = date.today().isoformat(); save(d); self.destroy(); app.refresh()
        ctk.CTkButton(self, text="Salvar e refazer cronograma", command=ok, **PRIMARY).pack(pady=12)
