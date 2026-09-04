import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from datetime import datetime, timezone
import data


# ---------- CONTROLLO RISCHIO ACCOUNT ----------
# NOTA IMPORTANTE: Discord non fornisce alcuna API che indichi se un account
# ha "bot nuke/raid" collegati o installati: questa informazione non esiste
# e nessun bot può leggerla. Quello che segue è un controllo EURISTICO basato
# su segnali pubblici (età account, avatar, nome) più una blacklist gestita
# manualmente dallo staff (es. ID noti di account usati in raid/nuke passati).
# Serve a segnalare account sospetti allo staff, NON a bloccare la verifica
# in automatico.

ACCOUNT_AGE_WARNING_DAYS = 7      # sotto questa soglia: account molto giovane
SUSPICIOUS_NAME_KEYWORDS = ["nuke", "raid", "selfbot", "nitro.gg", "discord.gift"]


def check_account_risk(member: discord.Member, blacklist: dict) -> list[str]:
    """Restituisce una lista di motivi di sospetto (vuota se l'account sembra pulito)."""
    reasons = []

    # 1. Blacklist manuale (ID segnalati in precedenza dallo staff)
    if str(member.id) in blacklist:
        reason = blacklist[str(member.id)].get("reason", "Segnalato in precedenza")
        reasons.append(f"⚠️ Account in blacklist: {reason}")

    # 2. Età dell'account
    age_days = (datetime.now(timezone.utc) - member.created_at).days
    if age_days < ACCOUNT_AGE_WARNING_DAYS:
        reasons.append(f"🆕 Account creato solo {age_days} giorni fa")

    # 3. Avatar di default (nessun avatar personalizzato)
    if member.avatar is None:
        reasons.append("🖼️ Nessun avatar personalizzato")

    # 4. Nome utente/global name con parole chiave sospette
    names_to_check = [member.name, member.global_name or ""]
    for name in names_to_check:
        lowered = name.lower()
        for kw in SUSPICIOUS_NAME_KEYWORDS:
            if kw in lowered:
                reasons.append(f"📛 Nome sospetto (contiene '{kw}')")
                break

    return reasons


class VerifyView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Verificati ora", style=discord.ButtonStyle.green, emoji="✅", custom_id="verify_button")
    async def verify_button(self, interaction: discord.Interaction, button: Button):
        settings = data.load("settings").get(str(interaction.guild.id), {})
        verified_id = settings.get("verified_role")
        unverified_id = settings.get("unverified_role")

        if not verified_id:
            return await interaction.response.send_message(
                "❌ Il ruolo verificato non è stato configurato. Contatta uno staff.", ephemeral=True
            )

        verified_role = interaction.guild.get_role(verified_id)
        if not verified_role:
            return await interaction.response.send_message(
                "❌ Il ruolo verificato configurato non esiste più. Contatta uno staff.", ephemeral=True
            )

        if verified_role in interaction.user.roles:
            return await interaction.response.send_message("✅ Sei già verificato!", ephemeral=True)

        # ---- Controllo rischio account (euristico, non bloccante) ----
        blacklist = data.load("blacklist").get(str(interaction.guild.id), {})
        risk_reasons = check_account_risk(interaction.user, blacklist)

        # Assegna il ruolo verificato
        try:
            await interaction.user.add_roles(verified_role, reason="Verifica completata")
        except discord.Forbidden:
            return await interaction.response.send_message(
                "❌ Non ho i permessi per assegnarti il ruolo verificato.", ephemeral=True
            )

        # Rimuove il ruolo non verificato, se configurato e presente
        if unverified_id:
            unverified_role = interaction.guild.get_role(unverified_id)
            if unverified_role and unverified_role in interaction.user.roles:
                try:
                    await interaction.user.remove_roles(unverified_role, reason="Verifica completata")
                except discord.Forbidden:
                    pass

        # Se l'account risulta sospetto, avvisa lo staff (nessun blocco automatico)
        if risk_reasons:
            settings = data.load("settings").get(str(interaction.guild.id), {})
            log_id = settings.get("welcome_goodbye_log")
            log_channel = interaction.guild.get_channel(log_id) if log_id else None
            if log_channel:
                embed = discord.Embed(
                    title="🚨 Verifica sospetta",
                    description=f"{interaction.user.mention} si è verificato ma presenta segnali sospetti:",
                    color=discord.Color.red()
                )
                embed.add_field(name="Motivi", value="\n".join(risk_reasons), inline=False)
                embed.set_footer(text=f"ID: {interaction.user.id}")
                await log_channel.send(embed=embed)

        await interaction.response.send_message("✅ Verifica completata con successo! Benvenuto nel server.", ephemeral=True)


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(VerifyView())

    # ---------- WELCOME / GOODBYE ----------
    @commands.hybrid_command(name="setwelcome", description="Imposta il canale di benvenuto")
    @commands.has_permissions(administrator=True)
    async def setwelcome(self, ctx, channel: discord.TextChannel):
        settings = data.load("settings")
        g = settings.setdefault(str(ctx.guild.id), {})
        g["welcome_channel"] = channel.id
        data.save("settings", settings)
        await ctx.send(f"✅ Canale di benvenuto impostato su {channel.mention}")

    @commands.hybrid_command(name="setgoodbye", description="Imposta il canale di addio")
    @commands.has_permissions(administrator=True)
    async def setgoodbye(self, ctx, channel: discord.TextChannel):
        settings = data.load("settings")
        g = settings.setdefault(str(ctx.guild.id), {})
        g["goodbye_channel"] = channel.id
        data.save("settings", settings)
        await ctx.send(f"✅ Canale di addio impostato su {channel.mention}")

    @commands.hybrid_command(name="setwelcomegoodbyelogs", description="Imposta il canale log welcome/goodbye")
    @commands.has_permissions(administrator=True)
    async def setwelcomegoodbyelogs(self, ctx, channel: discord.TextChannel):
        settings = data.load("settings")
        g = settings.setdefault(str(ctx.guild.id), {})
        g["welcome_goodbye_log"] = channel.id
        data.save("settings", settings)
        await ctx.send(f"✅ Canale log welcome/goodbye impostato su {channel.mention}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        settings = data.load("settings").get(str(member.guild.id), {})

        # Assegna il ruolo "non verificato" configurato, se esiste
        unverified_id = settings.get("unverified_role")
        if unverified_id:
            role = member.guild.get_role(unverified_id)
            if role:
                try:
                    await member.add_roles(role, reason="Nuovo membro: assegnazione ruolo non verificato")
                except discord.Forbidden:
                    pass

        channel_id = settings.get("welcome_channel")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                await channel.send(f"👋 Benvenuto {member.mention} su **{member.guild.name}**!")

        log_id = settings.get("welcome_goodbye_log")
        if log_id:
            log = member.guild.get_channel(log_id)
            if log:
                await log.send(f"📥 {member} è entrato nel server.")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        settings = data.load("settings").get(str(member.guild.id), {})
        channel_id = settings.get("goodbye_channel")
        if channel_id:
            channel = member.guild.get_channel(channel_id)
            if channel:
                await channel.send(f"👋 {member.mention} ha lasciato il server.")
        log_id = settings.get("welcome_goodbye_log")
        if log_id:
            log = member.guild.get_channel(log_id)
            if log:
                await log.send(f"📤 {member} ha lasciato il server.")

    # ---------- VERIFICA ----------
    @commands.hybrid_command(name="verifica", description="Invia il messaggio di verifica")
    @commands.has_permissions(administrator=True)
    async def verifica(self, ctx):
        embed = discord.Embed(
            title="✅ VERIFICA DI SICUREZZA ⚠️",
            description=(
                "Benvenuto! Per accedere al resto del server devi verificarti.\n\n"
                "**Come funziona:**\n"
                "1️⃣ Premi il pulsante ✅ **Verificati ora** qui sotto\n"
                "2️⃣ Il sistema controlla il tuo account (età, avatar, blacklist globale)\n"
                "3️⃣ Se tutto è a posto ricevi subito il ruolo ✅ `Verificato`\n\n"
                "Questo protegge il server da account falsi, alt e bot spam.\n"
                "Se il controllo segnala qualcosa di sospetto, lo staff verrà avvisato "
                "ma potrai comunque verificarti — nessun ban automatico."
            ),
            color=discord.Color.gold()
        )
        embed.set_footer(text="Fire security")
        await ctx.send(embed=embed, view=VerifyView())

    # ---------- CONFIGURAZIONE RUOLI VERIFICA ----------
    @commands.hybrid_command(name="roleverified", description="Configura il ruolo da assegnare quando un utente si verifica")
    @commands.has_permissions(administrator=True)
    async def roleverified(self, ctx, role: discord.Role):
        settings = data.load("settings")
        g = settings.setdefault(str(ctx.guild.id), {})
        g["verified_role"] = role.id
        data.save("settings", settings)
        await ctx.send(f"✅ Ruolo verificato impostato su {role.mention}")

    @commands.hybrid_command(name="roleunverified", description="Configura il ruolo non verificato da rimuovere quando l'utente si verifica")
    @commands.has_permissions(administrator=True)
    async def roleunverified(self, ctx, role: discord.Role):
        settings = data.load("settings")
        g = settings.setdefault(str(ctx.guild.id), {})
        g["unverified_role"] = role.id
        data.save("settings", settings)
        await ctx.send(f"✅ Ruolo non verificato impostato su {role.mention}")

    # ---------- USERINFO / SERVERINFO ----------
    @commands.hybrid_command(name="userinfo", description="Mostra le info di un utente")
    async def userinfo(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        embed = discord.Embed(title=f"Info su {member}", color=member.color)
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="ID", value=member.id)
        embed.add_field(name="Account creato", value=discord.utils.format_dt(member.created_at, "R"))
        embed.add_field(name="Entrato il", value=discord.utils.format_dt(member.joined_at, "R"))
        embed.add_field(name="Ruoli", value=", ".join(r.mention for r in member.roles[1:]) or "Nessuno", inline=False)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="serverinfo", description="Mostra le info del server")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(title=guild.name, color=discord.Color.blue())
        embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Membri", value=guild.member_count)
        embed.add_field(name="Creato il", value=discord.utils.format_dt(guild.created_at, "R"))
        embed.add_field(name="Proprietario", value=guild.owner.mention if guild.owner else "N/A")
        embed.add_field(name="Canali", value=len(guild.channels))
        embed.add_field(name="Ruoli", value=len(guild.roles))
        await ctx.send(embed=embed)

    # ---------- BLACKLIST (segnali di rischio account) ----------
    @commands.hybrid_command(name="blacklistadd", description="Segnala un account come sospetto (verrà avvisato lo staff se prova a verificarsi)")
    @commands.has_permissions(administrator=True)
    async def blacklistadd(self, ctx, user: discord.User, *, motivo: str = "Nessun motivo specificato"):
        bl = data.load("blacklist")
        g = bl.setdefault(str(ctx.guild.id), {})
        g[str(user.id)] = {"reason": motivo, "added_by": ctx.author.id}
        data.save("blacklist", bl)
        await ctx.send(f"✅ {user.mention} aggiunto alla blacklist. Motivo: {motivo}")

    @commands.hybrid_command(name="blacklistremove", description="Rimuove un account dalla blacklist")
    @commands.has_permissions(administrator=True)
    async def blacklistremove(self, ctx, user: discord.User):
        bl = data.load("blacklist")
        g = bl.setdefault(str(ctx.guild.id), {})
        if str(user.id) in g:
            del g[str(user.id)]
            data.save("blacklist", bl)
            await ctx.send(f"✅ {user.mention} rimosso dalla blacklist.")
        else:
            await ctx.send(f"❌ {user.mention} non è in blacklist.")

    @commands.hybrid_command(name="blacklistlist", description="Mostra gli account in blacklist")
    @commands.has_permissions(administrator=True)
    async def blacklistlist(self, ctx):
        bl = data.load("blacklist").get(str(ctx.guild.id), {})
        if not bl:
            return await ctx.send("✅ Nessun account in blacklist.")
        embed = discord.Embed(title="🚫 Blacklist account", color=discord.Color.dark_red())
        desc = ""
        for uid, info in bl.items():
            desc += f"<@{uid}> — {info.get('reason', 'N/A')}\n"
        embed.description = desc
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Utility(bot))
