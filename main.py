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

# Elenco dei cog da caricare (nome file .py senza estensione)
COGS = [
    "automod",
    "economy",
    "moderation",
    "levelling",
    "fun",
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
    # Stampa la working directory e i file .py presenti, utile per debug su Railway
    cwd = os.getcwd()
    py_files = [f for f in os.listdir(cwd) if f.endswith(".py")]
    print(f"📂 Working directory: {cwd}")
    print(f"📄 File .py trovati: {py_files}")

    for cog in COGS:
        expected_file = f"{cog}.py"
        if expected_file not in py_files:
            print(f"❌ File mancante per il cog '{cog}': non trovo '{expected_file}' in {cwd}")
            continue
        try:
            await bot.load_extension(cog)
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
