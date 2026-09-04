import discord
from discord.ext import commands
import config


# ---------------- DATI DEI COMANDI PER CATEGORIA ----------------

CATEGORIES = {
    "💰 Economy": {
        "emoji": "💰",
        "commands": [
            ("balance [member]", "Mostra il saldo tuo o di un altro utente"),
            ("work", "Lavora per guadagnare monete (cooldown 1h)"),
            ("daily", "Ricompensa giornaliera (cooldown 24h)"),
            ("mine", "Scava per trovare risorse (cooldown 30min)"),
            ("luckybox", "Apri la lucky box gratuita giornaliera"),
            ("lucky", "Aumenta la tua fortuna di 1 punto (cooldown 5min)"),
            ("pay <member> <amount>", "Trasferisci monete a un utente"),
            ("add <member> <amount>", "🔒 Admin: aggiunge monete a un utente"),
            ("remove <member> <amount>", "🔒 Admin: rimuove monete a un utente"),
            ("coinflip <amount> <testa/croce>", "Scommetti su testa o croce"),
            ("tris [amount]", "Gioca a tris contro il bot"),
            ("blackjack <amount>", "Gioca a blackjack"),
            ("roulette <amount> <rosso/nero/verde>", "Gioca alla roulette"),
            ("inventory [member]", "Mostra il tuo inventario"),
            ("shop", "Mostra lo shop delle box"),
            ("openbox <box_type>", "Apri una box del negozio"),
        ],
    },
    "🛡️ Moderation": {
        "emoji": "🛡️",
        "commands": [
            ("pex <member> <role>", "🔒 Assegna un ruolo a un utente"),
            ("depex <member> <role>", "🔒 Rimuove un ruolo a un utente"),
            ("ban <member> [reason]", "🔒 Banna un utente"),
            ("unban <user_id>", "🔒 Rimuove il ban a un utente"),
            ("kick <member> [reason]", "🔒 Espelle un utente"),
            ("warn <member> [reason]", "🔒 Warna un utente"),
            ("clearwarn <member>", "🔒 Rimuove tutti i warn di un utente"),
            ("showwarn <member>", "Mostra i warn di un utente"),
            ("mute <member> <minutes> [reason]", "🔒 Mette in timeout un utente"),
            ("unmute <member>", "🔒 Rimuove il timeout a un utente"),
            ("purge <amount>", "🔒 Cancella N messaggi"),
            ("lock", "🔒 Blocca il canale"),
            ("unlock", "🔒 Sblocca il canale"),
            ("slowmode <seconds>", "🔒 Imposta lo slowmode del canale"),
            ("changename <member> <new_name>", "🔒 Cambia il nickname di un utente"),
            ("messagecount [member]", "Mostra i messaggi conteggiati di un utente"),
            ("messageadd <member> <amount>", "🔒 Aggiunge messaggi a un utente"),
            ("messageremove <member> <amount>", "🔒 Rimuove messaggi a un utente"),
        ],
    },
    "📊 Leveling": {
        "emoji": "📊",
        "commands": [
            ("rank [member]", "Mostra il tuo livello o quello di un altro utente"),
            ("ranking", "Quanto ti manca al prossimo livello"),
            ("levelleaderboard", "Top 10 livelli del server"),
        ],
    },
    "🎉 Fun": {
        "emoji": "🎉",
        "commands": [
            ("8ball <question>", "Chiedi alla palla magica"),
            ("say <message>", "🔒 Il bot ripete un messaggio"),
            ("kiss <member>", "Bacia un utente"),
            ("kill <member>", "Uccidi (per gioco) un utente"),
            ("slap <member>", "Schiaffeggia un utente"),
            ("clap <member>", "Applaudi un utente"),
            ("hug <member>", "Abbraccia un utente"),
            ("marry <member>", "Sposa un utente"),
            ("divorce <member>", "Divorzia da un utente"),
            ("fakenitro", "Genera un finto regalo Nitro (per scherzo)"),
            ("ship <member1> [member2]", "Calcola la compatibilità tra due utenti"),
            ("rendigay [member]", "Mostra una percentuale a caso (per scherzo)"),
            ("aura [member]", "Calcola l'aura di un utente"),
        ],
    },
    "🛠️ Automod": {
        "emoji": "🛠️",
        "commands": [
            ("automod <on/off>", "🔒 Attiva/disattiva l'automod"),
            ("automodlinks <on/off>", "🔒 Attiva/disattiva il filtro link"),
            ("automodspam <on/off>", "🔒 Attiva/disattiva il filtro spam"),
            ("automodlogset <channel>", "🔒 Imposta il canale log automod"),
        ],
    },
    "⚙️ Utility": {
        "emoji": "⚙️",
        "commands": [
            ("setwelcome <channel>", "🔒 Imposta il canale di benvenuto"),
            ("setgoodbye <channel>", "🔒 Imposta il canale di addio"),
            ("setwelcomegoodbyelogs <channel>", "🔒 Imposta il canale log welcome/goodbye"),
            ("verifica", "🔒 Invia il messaggio con il bottone di verifica"),
            ("roleverified <role>", "🔒 Configura il ruolo assegnato alla verifica"),
            ("roleunverified <role>", "🔒 Configura il ruolo non verificato da rimuovere"),
            ("userinfo [member]", "Mostra le info di un utente"),
            ("serverinfo", "Mostra le info del server"),
            ("blacklistadd <user> [motivo]", "🔒 Segnala un account come sospetto"),
            ("blacklistremove <user>", "🔒 Rimuove un account dalla blacklist"),
            ("blacklistlist", "🔒 Mostra gli account in blacklist"),
        ],
    },
}


def build_category_embed(guild: discord.Guild, category_name: str) -> discord.Embed:
    data = CATEGORIES[category_name]
    embed = discord.Embed(
        title=f"{data['emoji']} Comandi - {category_name.split(' ', 1)[1]}",
        description="I comandi funzionano sia con `.` che con `/`.\n🔒 = richiede permessi specifici",
        color=config.EMBED_COLOR,
    )
    for name, desc in data["commands"]:
        embed.add_field(name=f"`{name}`", value=desc, inline=False)
    embed.set_footer(text=f"{guild.name if guild else 'Fire Bot'} • Usa il menu qui sotto per cambiare categoria")
    return embed


def build_home_embed(guild: discord.Guild) -> discord.Embed:
    embed = discord.Embed(
        title="🔥 Fire Bot - Centro Assistenza",
        description=(
            "Benvenuto! Qui trovi tutti i comandi disponibili, divisi per categoria.\n\n"
            "Usa il menu a tendina qui sotto per esplorare una categoria.\n"
            "Tutti i comandi funzionano sia come prefisso `.` che come slash `/`."
        ),
        color=config.EMBED_COLOR,
    )
    for category_name, data in CATEGORIES.items():
        embed.add_field(
            name=f"{data['emoji']} {category_name.split(' ', 1)[1]}",
            value=f"{len(data['commands'])} comandi",
            inline=True,
        )
    embed.set_footer(text=f"{guild.name if guild else 'Fire Bot'}")
    return embed


class HelpSelect(discord.ui.Select):
    def __init__(self, guild: discord.Guild):
        self.guild = guild
        options = [
            discord.SelectOption(
                label=category_name.split(" ", 1)[1],
                value=category_name,
                emoji=data["emoji"],
            )
            for category_name, data in CATEGORIES.items()
        ]
        options.insert(0, discord.SelectOption(label="Home", value="__home__", emoji="🏠"))
        super().__init__(placeholder="📂 Scegli una categoria...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        value = self.values[0]
        if value == "__home__":
            embed = build_home_embed(self.guild)
        else:
            embed = build_category_embed(self.guild, value)
        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, guild: discord.Guild, author: discord.abc.User, timeout: int = 120):
        super().__init__(timeout=timeout)
        self.author = author
        self.message = None
        self.add_item(HelpSelect(guild))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message(
                "❌ Solo chi ha usato il comando può interagire con questo menu.", ephemeral=True
            )
            return False
        return True

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Mostra la lista dei comandi del bot")
    async def help(self, ctx: commands.Context):
        embed = build_home_embed(ctx.guild)
        view = HelpView(ctx.guild, ctx.author)
        message = await ctx.send(embed=embed, view=view)
        view.message = message


async def setup(bot):
    await bot.add_cog(Help(bot))
