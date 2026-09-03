import discord
from discord.ext import commands
from datetime import timedelta
import re
import time
import data
import config

URL_REGEX = re.compile(r"(https?://\S+|www\.\S+|discord\.gg/\S+)")


class AutoMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spam_tracker = {}

    def get_settings(self, guild_id):
        settings = data.load("automod")
        g = settings.setdefault(str(guild_id), {
            "enabled": False,
            "links": False,
            "spam": False,
            "log_channel": None,
        })
        return settings, g

    @commands.hybrid_command(name="automod", description="Attiva/disattiva l'automod")
    @commands.has_permissions(administrator=True)
    async def automod(self, ctx, state: str):
        settings, g = self.get_settings(ctx.guild.id)
        g["enabled"] = state.lower() == "on"
        data.save("automod", settings)
        await ctx.send(f"🛡️ Automod {'attivato' if g['enabled'] else 'disattivato'}")

    @commands.hybrid_command(name="automodlinks", description="Attiva/disattiva il filtro link")
    @commands.has_permissions(administrator=True)
    async def automodlinks(self, ctx, state: str):
        settings, g = self.get_settings(ctx.guild.id)
        g["links"] = state.lower() == "on"
        data.save("automod", settings)
        await ctx.send(f"🔗 Filtro link {'attivato' if g['links'] else 'disattivato'}")

    @commands.hybrid_command(name="automodspam", description="Attiva/disattiva il filtro spam")
    @commands.has_permissions(administrator=True)
    async def automodspam(self, ctx, state: str):
        settings, g = self.get_settings(ctx.guild.id)
        g["spam"] = state.lower() == "on"
        data.save("automod", settings)
        await ctx.send(f"🚫 Filtro spam {'attivato' if g['spam'] else 'disattivato'}")

    @commands.hybrid_command(name="automodlogset", description="Imposta il canale log automod")
    @commands.has_permissions(administrator=True)
    async def automodlogset(self, ctx, channel: discord.TextChannel):
        settings, g = self.get_settings(ctx.guild.id)
        g["log_channel"] = channel.id
        data.save("automod", settings)
        await ctx.send(f"📝 Canale log automod impostato su {channel.mention}")

    async def log_action(self, guild, g, text):
        if g["log_channel"]:
            channel = guild.get_channel(g["log_channel"])
            if channel:
                await channel.send(text)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        settings, g = self.get_settings(message.guild.id)
        if not g["enabled"]:
            return

        # Filtro link
        if g["links"] and URL_REGEX.search(message.content):
            if not message.author.guild_permissions.manage_messages:
                await message.delete()
                try:
                    await message.author.timeout(timedelta(minutes=5), reason="Automod: link non autorizzato")
                except discord.Forbidden:
                    pass
                await message.channel.send(f"🔗 {message.author.mention} timeout 5 minuti per link non autorizzato.", delete_after=5)
                await self.log_action(message.guild, g, f"🔗 {message.author} timeout per link: {message.content[:200]}")
                return

        # Filtro spam (5 messaggi in 5 secondi)
        if g["spam"]:
            uid = message.author.id
            now = time.time()
            entries = self.spam_tracker.setdefault(uid, [])
            entries.append(now)
            entries[:] = [t for t in entries if now - t < 5]
            if len(entries) >= 5:
                try:
                    await message.author.timeout(timedelta(minutes=5), reason="Automod: spam")
                except discord.Forbidden:
                    pass
                await message.channel.send(f"🚫 {message.author.mention} timeout 5 minuti per spam.", delete_after=5)
                await self.log_action(message.guild, g, f"🚫 {message.author} timeout per spam")
                entries.clear()


async def setup(bot):
    await bot.add_cog(AutoMod(bot))
