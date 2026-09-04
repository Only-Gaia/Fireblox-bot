import asyncio
import os
import discord
from discord.ext import commands
import config

intents = discord.Intents.default()
intents.message_content = True  # necessario per i comandi con prefisso "."
intents.members = True

bot = commands.Bot(
    command_prefix=config.PREFIX,
    intents=intents,
    help_command=None,  # help personalizzato in help.py
)

COGS_DIR = "cogs"

# Elenco dei cog da caricare (nome file .py senza estensione, dentro cogs/)
COGS = [
    "automod",
    "economy",
    "moderation",
    "levelling",
    "fun",
    "utility",
    "help",
]


@bot.event
async def on_ready():
    print(f"✅ Bot connesso come {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"🔄 Sincronizzati {len(synced)} comandi slash (/)")
    except Exception as e:
        print(f"⚠️ Errore durante la sincronizzazione dei comandi slash: {e}")
    print("🤖 Bot pronto! Comandi disponibili sia con '.' che con '/'.")


async def load_cogs():
    cwd = os.getcwd()
    cogs_path = os.path.join(cwd, COGS_DIR)
    print(f"📁 Working directory: {cwd}")

    if not os.path.isdir(cogs_path):
        print(f"❌ Cartella '{COGS_DIR}/' non trovata in {cwd}! Controlla che sia stata pushata su GitHub.")
        return

    py_files = [f for f in os.listdir(cogs_path) if f.endswith(".py")]
    print(f"📄 File .py trovati in {COGS_DIR}/: {py_files}")

    for cog in COGS:
        expected_file = f"{cog}.py"
        if expected_file not in py_files:
            print(f"❌ File mancante per il cog '{cog}': non trovo '{COGS_DIR}/{expected_file}'")
            continue
        try:
            await bot.load_extension(f"{COGS_DIR}.{cog}")
            print(f"✅ Cog caricato: {cog}")
        except Exception:
            import traceback
            print(f"❌ Errore caricamento cog '{cog}':")
            traceback.print_exc()


async def main():
    async with bot:
        await load_cogs()
        await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
