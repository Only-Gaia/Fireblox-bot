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

# ================= TICKET MM (Middle Man) =================
MAX_STAFF_ROLES = 15                 # limite massimo di ruoli staff configurabili con /rolestaff
MM_CHANNEL_PREFIX = "mm-"            # prefisso del nome canale creato da /ticketmm
MM_PANEL_TITLE = "👮‍♂️ Richiedi un Middle Man"
MM_PANEL_DESCRIPTION = (
    "Se hai bisogno di un **Middle Man** per uno scambio sicuro, premi il pulsante qui sotto.\n\n"
    "Verrà creato un canale privato tra te e lo staff dove potrai spiegare la situazione."
)
MM_PANEL_FOOTER = "Fire security"
MM_BUTTON_LABEL = "Richiedi MM"
MM_BUTTON_EMOJI = "👮‍♂️"
