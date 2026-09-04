import discord
from discord import app_commands
from discord.ext import commands
from datetime import timedelta
import data


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        return True

    # ---------- PEX / DEPEX (assegna/rimuove ruolo) ----------
    @commands.hybrid_command(name="pex", description="Assegna un ruolo a un utente")
    @app_commands.describe(member="Utente", role="Ruolo")
    @commands.has_permissions(manage_roles=True)
    async def pex(self, ctx, member: discord.Member, role: discord.Role):
        await member.add_roles(role, reason=f"Pex da {ctx.author}")
        await ctx.send(f"✅ Ruolo {role.mention} assegnato a {member.mention}")

    @commands.hybrid_command(name="depex", description="Rimuove un ruolo a un utente")
    @app_commands.describe(member="Utente", role="Ruolo")
    @commands.has_permissions(manage_roles=True)
    async def depex(self, ctx, member: discord.Member, role: discord.Role):
        await member.remove_roles(role, reason=f"Depex da {ctx.author}")
        await ctx.send(f"✅ Ruolo {role.mention} rimosso a {member.mention}")

    # ---------- BAN / UNBAN ----------
    @commands.hybrid_command(name="ban", description="Banna un utente")
    @app_commands.describe(member="Utente", reason="Motivo")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = "Nessun motivo"):
        await member.ban(reason=reason)
        await ctx.send(f"🔨 {member.mention} è stato bannato. Motivo: {reason}")

    @commands.hybrid_command(name="unban", description="Rimuove il ban a un utente")
    @app_commands.describe(user_id="ID utente")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: str):
        user = await self.bot.fetch_user(int(user_id))
        await ctx.guild.unban(user)
        await ctx.send(f"✅ {user} sbannato")

    # ---------- KICK ----------
    @commands.hybrid_command(name="kick", description="Espelle un utente")
    @app_commands.describe(member="Utente", reason="Motivo")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = "Nessun motivo"):
        await member.kick(reason=reason)
        await ctx.send(f"👢 {member.mention} espulso. Motivo: {reason}")

    # ---------- WARN SYSTEM ----------
    @commands.hybrid_command(name="warn", description="Warna un utente")
    @app_commands.describe(member="Utente", reason="Motivo")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason: str = "Nessun motivo"):
        warns = data.load("warns")
        g = warns.setdefault(str(ctx.guild.id), {})
        u = g.setdefault(str(member.id), [])
        u.append({"reason": reason, "mod": str(ctx.author.id)})
        data.save("warns", warns)
        await ctx.send(f"⚠️ {member.mention} warnato. Motivo: {reason} (Totale: {len(u)})")

    @commands.hybrid_command(name="clearwarn", description="Rimuove tutti i warn di un utente")
    @app_commands.describe(member="Utente")
    @commands.has_permissions(manage_messages=True)
    async def clearwarn(self, ctx, member: discord.Member):
        warns = data.load("warns")
        g = warns.setdefault(str(ctx.guild.id), {})
        g[str(member.id)] = []
        data.save("warns", warns)
        await ctx.send(f"✅ Warn di {member.mention} rimossi")

    @commands.hybrid_command(name="showwarn", description="Mostra i warn di un utente")
    @app_commands.describe(member="Utente")
    async def showwarn(self, ctx, member: discord.Member):
        warns = data.load("warns")
        u = warns.get(str(ctx.guild.id), {}).get(str(member.id), [])
        if not u:
            return await ctx.send(f"{member.mention} non ha warn.")
        embed = discord.Embed(title=f"Warn di {member}", color=discord.Color.orange())
        for i, w in enumerate(u, 1):
            embed.add_field(name=f"Warn #{i}", value=f"Motivo: {w['reason']}", inline=False)
        await ctx.send(embed=embed)

    # ---------- MUTE / UNMUTE (timeout) ----------
    @commands.hybrid_command(name="mute", description="Mette in timeout un utente")
    @app_commands.describe(member="Utente", minutes="Minuti", reason="Motivo")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, minutes: int, *, reason: str = "Nessun motivo"):
        await member.timeout(timedelta(minutes=minutes), reason=reason)
        await ctx.send(f"🔇 {member.mention} mutato per {minutes} minuti. Motivo: {reason}")

    @commands.hybrid_command(name="unmute", description="Rimuove il timeout a un utente")
    @app_commands.describe(member="Utente")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member):
        await member.timeout(None)
        await ctx.send(f"🔊 {member.mention} smutato")

    # ---------- PURGE / CLEAR MESSAGGI ----------
    @commands.hybrid_command(name="purge", description="Cancella N messaggi")
    @app_commands.describe(amount="Numero di messaggi")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f"🧹 Cancellati {amount} messaggi")
        await msg.delete(delay=3)

    # ---------- LOCK / UNLOCK ----------
    @commands.hybrid_command(name="lock", description="Blocca il canale")
    @commands.has_permissions(manage_channels=True)
    async def lock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.send("🔒 Canale bloccato")

    @commands.hybrid_command(name="unlock", description="Sblocca il canale")
    @commands.has_permissions(manage_channels=True)
    async def unlock(self, ctx):
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=True)
        await ctx.send("🔓 Canale sbloccato")

    # ---------- SLOWMODE ----------
    @commands.hybrid_command(name="slowmode", description="Imposta slowmode in secondi")
    @app_commands.describe(seconds="Secondi")
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int):
        await ctx.channel.edit(slowmode_delay=seconds)
        await ctx.send(f"🐌 Slowmode impostato a {seconds}s")

    # ---------- CHANGENAME (cambia nickname a un utente) ----------
    @commands.hybrid_command(name="changename", description="Cambia il nickname di un utente")
    @app_commands.describe(member="Utente", new_name="Nuovo nome")
    @commands.has_permissions(manage_nicknames=True)
    async def changename(self, ctx, member: discord.Member, *, new_name: str):
        old_name = member.display_name
        try:
            await member.edit(nick=new_name, reason=f"Nome cambiato da {ctx.author}")
        except discord.Forbidden:
            return await ctx.send(
                "❌ Non ho i permessi per modificare il nickname di questo utente "
                "(probabilmente ha un ruolo più alto del mio)."
            )
        await ctx.send(f"✏️ Nome di {member.mention} cambiato da **{old_name}** a **{new_name}**")

    # ---------- MESSAGE COUNT MANAGEMENT ----------
    @commands.hybrid_command(name="messagecount", description="Mostra i messaggi di un utente")
    @app_commands.describe(member="Utente")
    async def messagecount(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        levels = data.load("levels")
        u = levels.get(str(ctx.guild.id), {}).get(str(member.id), {"messages": 0})
        await ctx.send(f"📨 {member.mention} ha {u['messages']} messaggi")

    @commands.hybrid_command(name="messageadd", description="Aggiunge messaggi a un utente")
    @app_commands.describe(member="Utente", amount="Quantità")
    @commands.has_permissions(manage_guild=True)
    async def messageadd(self, ctx, member: discord.Member, amount: int):
        levels, u = data.get_user_levels(ctx.guild.id, member.id)
        u["messages"] += amount
        data.save("levels", levels)
        await ctx.send(f"✅ Aggiunti {amount} messaggi a {member.mention}")

    @commands.hybrid_command(name="messageremove", description="Rimuove messaggi a un utente")
    @app_commands.describe(member="Utente", amount="Quantità")
    @commands.has_permissions(manage_guild=True)
    async def messageremove(self, ctx, member: discord.Member, amount: int):
        levels, u = data.get_user_levels(ctx.guild.id, member.id)
        u["messages"] = max(0, u["messages"] - amount)
        data.save("levels", levels)
        await ctx.send(f"✅ Rimossi {amount} messaggi a {member.mention}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
