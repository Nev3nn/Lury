import json, os, sys, copy
# Empacotado (PyInstaller --onefile): usa a pasta do .exe, não a pasta temporária
BASE = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(BASE, "data.json")
TIMER_DEFAULT = {"focus": 25, "short": 5, "long": 15, "cycles": 4, "mode": "Pomodoro"}
DEFAULT = {"per_day": 2, "schedule_date": "", "reminded": "", "cards": [], "timer": dict(TIMER_DEFAULT), "points": 0, "items": [], "subjects": {}, "daily_goal_h": 2.0, "schedule": {},
           "todo": {}, "sessions": {}, "simulados": [], "last_adjust": 0,
           "streak_miss": 0, "penalty_log": [], "last_checked": ""}

def load():
    d = copy.deepcopy(DEFAULT)
    if os.path.exists(PATH):
        try:
            with open(PATH, encoding="utf-8") as f:
                d.update(json.load(f))
        except (OSError, ValueError):
            pass
    return d

def save(d):
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)
