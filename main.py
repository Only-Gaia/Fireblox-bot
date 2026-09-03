import asyncio
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
    for cog in COGS:
        try:
            await bot.load_extension(cog)
            print(f"✅ Cog caricato: {cog}")
        except Exception as e:
            print(f"❌ Errore caricamento cog '{cog}': {e}")


async def main():
    async with bot:
        await load_cogs()
        await bot.start(config.BOT_TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
