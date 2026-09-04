import json
import os

DATA_DIR = "data_files"
os.makedirs(DATA_DIR, exist_ok=True)

# Nomi dei "file" di dati conosciuti dal bot.
# Nuovi nomi vengono comunque aggiunti automaticamente al primo save().
FILES = {
    "automod",
    "economy",
    "warns",
    "levels",
    "marriages",
}


def _path(name):
    return os.path.join(DATA_DIR, f"{name}.json")


def load(name):
    """Carica il contenuto del file JSON `name`. Ritorna {} se non esiste."""
    FILES.add(name)
    path = _path(name)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}


def save(name, obj):
    """Salva `obj` nel file JSON `name`."""
    FILES.add(name)
    with open(_path(name), "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4, ensure_ascii=False)


# ---------------- HELPER ECONOMIA ----------------
def get_user_economy(guild_id, user_id):
    """Ritorna (dati_completi_economy, dati_utente) creando i default se mancanti."""
    econ = load("economy")
    guild = econ.setdefault(str(guild_id), {})
    user = guild.setdefault(str(user_id), {
        "balance": 0,
        "last_work": 0,
        "last_daily": 0,
        "last_mine": 0,
        "last_luckybox": 0,
        "luck": 0,
        "inventory": {},
    })
    return econ, user


# ---------------- HELPER LIVELLI ----------------
def get_user_levels(guild_id, user_id):
    """Ritorna (dati_completi_levels, dati_utente) creando i default se mancanti."""
    levels = load("levels")
    guild = levels.setdefault(str(guild_id), {})
    user = guild.setdefault(str(user_id), {
        "level": 0,
        "messages": 0,
    })
    return levels, user
