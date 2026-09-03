import os

# ================= BOT =================
BOT_TOKEN = os.getenv("BOT_TOKEN", "INSERISCI_QUI_IL_TUO_TOKEN")
PREFIX = "."  # prefisso per i comandi testuali (in aggiunta agli slash "/")
OWNER_IDS = []  # ID Discord dei proprietari/admin principali del bot

EMBED_COLOR = 0xFFA500

# ================= ECONOMIA =================
CURRENCY_NAME = "Fire Coins"

BOX_PRICES = {
    "comuni": 100,
    "rare": 500,
    "epiche": 1500,
    "mitiche": 5000,
    "leggendaria": 15000,
}

