"""Regras do app: cronograma, penalidades e reajuste por simulados."""
from datetime import date, timedelta

DAYS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
PTS_PER_MIN = 10

def weekly_minutes(subjects, daily_h):
    """soma pesos -> horas/dia x 7 -> minutos semanais / soma = fator por ponto -> fator x peso."""
    total_w = sum(subjects.values())
    if total_w <= 0:
        return {}
    base = daily_h * 7 * 60 / total_w
    return {s: round(base * w) for s, w in subjects.items() if w > 0}

def build_schedule(subjects, daily_h):
    """Divide cada matéria em sessões de ~45 min e as põe nos dias menos carregados."""
    sched = {d: [] for d in DAYS}
    load = [0] * 7
    for s, m in sorted(weekly_minutes(subjects, daily_h).items(), key=lambda x: -x[1]):
        n = min(7, max(1, round(m / 45)))
        chunk, rem = divmod(m, n)
        days = sorted(sorted(range(7), key=lambda i: (load[i], i))[:n])
        for k, i in enumerate(days):
            t = chunk + (rem if k == 0 else 0)
            sched[DAYS[i]].append({"subject": s, "minutes": t})
            load[i] += t
    return sched

def week_days():
    t = date.today()
    mon = t - timedelta(t.weekday())
    return [mon + timedelta(i) for i in range(7)]

def studied(d, day, subj="total"):
    return d["sessions"].get(day.isoformat(), {}).get(subj, 0)

def goal_min(d):
    return int(d["daily_goal_h"] * 60)

def apply_penalties(d):
    """A partir do 2º dia seguido sem bater a meta, perde 50 pts x dias seguidos."""
    today, last = date.today(), d.get("last_checked")
    d["last_checked"] = today.isoformat()
    if not last or not d["schedule"]:
        return
    day = date.fromisoformat(last)
    while day < today:
        if studied(d, day) >= goal_min(d):
            d["streak_miss"] = 0
        else:
            d["streak_miss"] += 1
            if d["streak_miss"] >= 2:
                loss = min(d["points"], 50 * d["streak_miss"])
                d["points"] -= loss
                d["penalty_log"].append({"date": day.isoformat(), "loss": loss, "streak": d["streak_miss"]})
        day += timedelta(1)

def propose_adjustment(d):
    """Compara os 2 últimos simulados; nota menor/queda => peso maior."""
    a, b = d["simulados"][-2:]
    new, changes = {}, []
    for s, w in d["subjects"].items():
        if w == 0 or s not in a["scores"] or s not in b["scores"]:
            new[s] = w
            continue
        avg = (a["scores"][s] + b["scores"][s]) / 2
        delta = b["scores"][s] - a["scores"][s]
        step = (avg < 6) + (avg < 4) - (avg >= 8) + (delta <= -1) - (delta >= 1)
        new[s] = max(1, min(5, w + max(-2, min(2, step))))
        changes.append((s, w, new[s], avg, delta))
    return new, changes, build_schedule(new, d["daily_goal_h"])

def schedule_card(c, grade):
    """Espaçamento estilo Anki. grade: 0 Errei, 1 Difícil, 2 Bom, 3 Fácil."""
    if grade == 0:
        c["reps"], c["interval"] = 0, 0
        c["ease"] = max(1.3, c["ease"] - 0.2)
    else:
        c["ease"] = max(1.3, c["ease"] + (-0.15, 0, 0.15)[grade - 1])
        if c["reps"] == 0: iv = (1, 1, 3)[grade - 1]
        elif c["reps"] == 1: iv = (2, 4, 6)[grade - 1]
        else: iv = max(c["interval"] + 1, round(c["interval"] * c["ease"] * (0.8, 1, 1.3)[grade - 1]))
        c["interval"], c["reps"] = iv, c["reps"] + 1
    c["due"] = (date.today() + timedelta(c["interval"])).isoformat()
