import discord
from discord import app_commands
from discord.ext import commands
import random
import time
import data
import config


def cooldown_left(last_ts, seconds):
    remaining = seconds - (time.time() - last_ts)
    return max(0, remaining)


# ==================== TRIS (TIC TAC TOE) INTERATTIVO ====================

class TrisButton(discord.ui.Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TrisView = self.view

        if interaction.user.id != view.player.id:
            return await interaction.response.send_message(
                "❌ Non è la tua partita!", ephemeral=True
            )
        if view.game_over or view.board[self.y][self.x] is not None:
            return await interaction.response.defer()

        # ---- mossa del giocatore ----
        view.board[self.y][self.x] = "X"
        self.label = "❌"
        self.style = discord.ButtonStyle.danger
        self.disabled = True

        winner = view.check_winner()
        if winner or view.is_full():
            return await view.end_game(interaction, winner)

        # ---- mossa del bot ----
        view.bot_move()

        winner = view.check_winner()
        if winner or view.is_full():
            return await view.end_game(interaction, winner)

        await interaction.response.edit_message(embed=view.build_embed(), view=view)


class TrisView(discord.ui.View):
    def __init__(self, ctx, amount: int, timeout: int = 60):
        super().__init__(timeout=timeout)
        self.ctx = ctx
        self.player = ctx.author
        self.amount = amount
        self.board = [[None, None, None] for _ in range(3)]
        self.game_over = False
        self.message = None

        for y in range(3):
            for x in range(3):
                self.add_item(TrisButton(x, y))

    def is_full(self):
        return all(cell is not None for row in self.board for cell in row)

    def check_winner(self):
        b = self.board
        lines = []
        for i in range(3):
            lines.append([b[i][0], b[i][1], b[i][2]])  # righe
            lines.append([b[0][i], b[1][i], b[2][i]])  # colonne
        lines.append([b[0][0], b[1][1], b[2][2]])       # diagonale
        lines.append([b[0][2], b[1][1], b[2][0]])       # diagonale
        for line in lines:
            if line[0] is not None and line[0] == line[1] == line[2]:
                return line[0]
        return None

    def bot_move(self):
        empty = [(x, y) for y in range(3) for x in range(3) if self.board[y][x] is None]
        if not empty:
            return

        # 1) il bot vince subito se può
        for x, y in empty:
            self.board[y][x] = "O"
            if self.check_winner() == "O":
                self._apply_bot_button(x, y)
                return
            self.board[y][x] = None

        # 2) blocca il giocatore se sta per vincere
        for x, y in empty:
            self.board[y][x] = "X"
            player_would_win = self.check_winner() == "X"
            self.board[y][x] = None
            if player_would_win:
                self.board[y][x] = "O"
                self._apply_bot_button(x, y)
                return

        # 3) preferisce il centro se libero
        if self.board[1][1] is None:
            self.board[1][1] = "O"
            self._apply_bot_button(1, 1)
            return

        # 4) altrimenti mossa casuale
        x, y = random.choice(empty)
        self.board[y][x] = "O"
        self._apply_bot_button(x, y)

    def _apply_bot_button(self, x, y):
        for item in self.children:
            if isinstance(item, TrisButton) and item.x == x and item.y == y:
                item.label = "⭕"
                item.style = discord.ButtonStyle.primary
                item.disabled = True
                break

    def build_embed(self, result_text: str = None):
        embed = discord.Embed(title="❌⭕ Tris", color=config.EMBED_COLOR)
        embed.description = result_text or f"Turno di: {self.player.mention}"
        embed.set_footer(
            text=f"Puntata: {self.amount} {config.CURRENCY_NAME}" if self.amount else "Partita amichevole"
        )
        return embed

    async def end_game(self, interaction: discord.Interaction, winner):
        self.game_over = True
        for item in self.children:
            item.disabled = True

        econ, u = data.get_user_economy(self.ctx.guild.id, self.player.id)

        if winner == "X":
            if self.amount:
                u["balance"] += self.amount
                data.save("economy", econ)
            result_text = f"🎉 {self.player.mention} ha vinto contro il bot!"
            if self.amount:
                result_text += f" (+{self.amount} {config.CURRENCY_NAME})"
        elif winner == "O":
            if self.amount:
                u["balance"] -= self.amount
                data.save("economy", econ)
            result_text = f"🤖 Il bot ha vinto! {self.player.mention} ha perso."
            if self.amount:
                result_text += f" (-{self.amount} {config.CURRENCY_NAME})"
        else:
            result_text = f"🤝 Pareggio! {self.player.mention} non vince né perde nulla."

        self.stop()
        await interaction.response.edit_message(embed=self.build_embed(result_text), view=self)

    async def on_timeout(self):
        if self.game_over:
            return
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(
                    embed=self.build_embed(f"⏳ Partita scaduta, {self.player.mention} non ha giocato in tempo."),
                    view=self,
                )
            except discord.HTTPException:
                pass


# ==================== COG ECONOMY ====================

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # ---------- BALANCE ----------
    @commands.hybrid_command(name="balance", description="Mostra il tuo saldo")
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        econ, u = data.get_user_economy(ctx.guild.id, member.id)
        await ctx.send(f"💰 {member.mention} ha **{u['balance']}** {config.CURRENCY_NAME}")

    # ---------- WORK ----------
    @commands.hybrid_command(name="work", description="Lavora per guadagnare monete")
    async def work(self, ctx):
        econ, u = data.get_user_economy(ctx.guild.id, ctx.author.id)
        left = cooldown_left(u["last_work"], 3600)
        if left > 0:
            return await ctx.send(f"⏳ Aspetta ancora {int(left // 60)} minuti per lavorare di nuovo.")
        amount = random.randint(50, 200)
        u["balance"] += amount
        u["last_work"] = time.time()
        data.save("economy", econ)
        await ctx.send(f"💼 Hai lavorato e guadagnato **{amount}** {config.CURRENCY_NAME}!")

    # ---------- DAILY ----------
    @commands.hybrid_command(name="daily", description="Ricompensa giornaliera")
    async def daily(self, ctx):
        econ, u = data.get_user_economy(ctx.guild.id, ctx.author.id)
        left = cooldown_left(u["last_daily"], 86400)
        if left > 0:
            return await ctx.send(f"⏳ Torna tra {int(left // 3600)}h per la daily.")
        amount = 300
        u["balance"] += amount
        u["last_daily"] = time.time()
        data.save("economy", econ)
        await ctx.send(f"🎁 Hai ricevuto la daily: **{amount}** {config.CURRENCY_NAME}!")

    # ---------- MINE ----------
    @commands.hybrid_command(name="mine", description="Scava per trovare risorse")
    async def mine(self, ctx):
        econ, u = data.get_user_economy(ctx.guild.id, ctx.author.id)
        left = cooldown_left(u["last_mine"], 1800)
        if left > 0:
            return await ctx.send(f"⏳ Aspetta {int(left // 60)} minuti prima di scavare di nuovo.")
        amount = random.randint(20, 100)
        u["balance"] += amount
        u["last_mine"] = time.time()
        data.save("economy", econ)
        await ctx.send(f"⛏️ Hai scavato e trovato **{amount}** {config.CURRENCY_NAME}!")

    # ---------- LUCKYBOX (1 gratis al giorno) ----------
    @commands.hybrid_command(name="luckybox", description="Apri la lucky box gratuita giornaliera")
    async def luckybox(self, ctx):
        econ, u = data.get_user_economy(ctx.guild.id, ctx.author.id)
        left = cooldown_left(u["last_luckybox"], 86400)
        if left > 0:
            return await ctx.send(f"⏳ Lucky box disponibile tra {int(left // 3600)}h.")
        amount = random.randint(10, 500)
        u["balance"] += amount
        u["last_luckybox"] = time.time()
        data.save("economy", econ)
        await ctx.send(f"🎰 Hai aperto la Lucky Box e trovato **{amount}** {config.CURRENCY_NAME}!")

    # ---------- LUCKY (aumenta fortuna, cooldown 5 min) ----------
    @commands.hybrid_command(name="lucky", description="Aumenta la tua fortuna di 1 punto")
    @commands.cooldown(1, 300, commands.BucketType.user)
    async def lucky(self, ctx):
        econ, u = data.get_user_economy(ctx.guild.id, ctx.author.id)
        u["luck"] += 1
        data.save("economy", econ)
        await ctx.send(f"🍀 La tua fortuna è ora **{u['luck']}**!")

    # ---------- PAY ----------
    @commands.hybrid_command(name="pay", description="Trasferisci monete a un utente")
    @app_commands.describe(member="Destinatario", amount="Quantità")
    async def pay(self, ctx, member: discord.Member, amount: int):
        if amount <= 0:
            return await ctx.send("❌ Importo non valido.")
        econ, sender = data.get_user_economy(ctx.guild.id, ctx.author.id)
        if sender["balance"] < amount:
            return await ctx.send("❌ Saldo insufficiente.")
        _, receiver = data.get_user_economy(ctx.guild.id, member.id)
        sender["balance"] -= amount
        receiver["balance"] += amount
        data.save("economy", econ)
        await ctx.send(f"💸 {ctx.author.mention} ha inviato **{amount}** {config.CURRENCY_NAME} a {member.mention}")

    # ---------- ADD / REMOVE (admin) ----------
    @commands.hybrid_command(name="add", description="Aggiunge monete a un utente")
    @commands.has_permissions(administrator=True)
    async def add(self, ctx, member: discord.Member, amount: int):
        econ, u = data.get_user_economy(ctx.guild.id, member.id)
        u["balance"] += amount
        data.save("economy", econ)
        await ctx.send(f"✅ Aggiunti {amount} {config.CURRENCY_NAME} a {member.mention}")

    @commands.hybrid_command(name="remove", description="Rimuove monete a un utente")
    @commands.has_permissions(administrator=True)
    async def remove(self, ctx, member: discord.Member, amount: int):
        econ, u = data.get_user_economy(ctx.guild.id, member.id)
        u["balance"] = max(0, u["balance"] - amount)
        data.save("economy", econ)
        await ctx.send(f"✅ Rimossi {amount} {config.CURRENCY_NAME} a {member.mention}")

    # ---------- COINFLIP ----------
    @commands.hybrid_command(name="coinflip", description="Scommetti su testa o croce")
    @app_commands.describe(amount="Puntata", choice="testa/croce")
    async def coinflip(self, ctx, amount: int, choice: str):
        choice = choice.lower()
        if choice not in ("testa", "croce"):
            return await ctx.send("❌ Scegli 'testa' o 'croce'.")
        econ, u = data.get_user_economy(ctx.guild.id, ctx.author.id)
        if u["balance"] < amount:
            return await ctx.send("❌ Saldo insufficiente.")
        result = random.choice(["testa", "croce"])
        if result == choice:
            u["balance"] += amount
            msg = f"🪙 È uscito **{result}**! Hai vinto **{amount}**!"
        else:
            u["balance"] -= amount
            msg = f"🪙 È uscito **{result}**. Hai perso **{amount}**."
        data.save("economy", econ)
        await ctx.send(msg)

    # ---------- TRIS (contro il bot, tabellone interattivo) ----------
    @commands.hybrid_command(name="tris", description="Gioca a tris contro il bot")
    @app_commands.describe(amount="Puntata (opzionale)")
    async def tris(self, ctx, amount: int = 0):
        if amount:
            if amount < 0:
                return await ctx.send("❌ Importo non valido.")
            econ, u = data.get_user_economy(ctx.guild.id, ctx.author.id)
            if u["balance"] < amount:
                return await ctx.send("❌ Saldo insufficiente.")

        view = TrisView(ctx, amount)
        embed = view.build_embed()
        message = await ctx.send(embed=embed, view=view)
        view.message = message

    # ---------- BLACKJACK (semplificato) ----------
    @commands.hybrid_command(name="blackjack", description="Gioca a blackjack")
    @app_commands.describe(amount="Puntata")
    async def blackjack(self, ctx, amount: int):
        econ, u = data.get_user_economy(ctx.guild.id, ctx.author.id)
        if u["balance"] < amount:
            return await ctx.send("❌ Saldo insufficiente.")

        def draw_hand():
            return [random.randint(1, 11) for _ in range(2)]

        player = draw_hand()
        dealer = draw_hand()
        player_total = sum(player)
        dealer_total = sum(dealer)

        if player_total > dealer_total and player_total <= 21:
            u["balance"] += amount
            result = f"🃏 Hai vinto! ({player_total} vs {dealer_total}) +{amount}"
        elif player_total == dealer_total:
            result = f"🃏 Pareggio ({player_total} vs {dealer_total})"
        else:
            u["balance"] -= amount
            result = f"🃏 Hai perso ({player_total} vs {dealer_total}) -{amount}"
        data.save("economy", econ)
        await ctx.send(result)

    # ---------- ROULETTE ----------
    @commands.hybrid_command(name="roulette", description="Gioca alla roulette")
    @app_commands.describe(amount="Puntata", color="rosso/nero/verde")
    async def roulette(self, ctx, amount: int, color: str):
        color = color.lower()
        if color not in ("rosso", "nero", "verde"):
            return await ctx.send("❌ Scegli rosso, nero o verde.")
        econ, u = data.get_user_economy(ctx.guild.id, ctx.author.id)
        if u["balance"] < amount:
            return await ctx.send("❌ Saldo insufficiente.")
        outcome = random.choices(["rosso", "nero", "verde"], weights=[48, 48, 4])[0]
        if outcome == color:
            multiplier = 14 if color == "verde" else 2
            win = amount * multiplier
            u["balance"] += win
            msg = f"🎡 È uscito **{outcome}**! Hai vinto **{win}**!"
        else:
            u["balance"] -= amount
            msg = f"🎡 È uscito **{outcome}**. Hai perso **{amount}**."
        data.save("economy", econ)
        await ctx.send(msg)

    # ---------- INVENTORY ----------
    @commands.hybrid_command(name="inventory", description="Mostra il tuo inventario")
    async def inventory(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        econ, u = data.get_user_economy(ctx.guild.id, member.id)
        if not u["inventory"]:
            return await ctx.send(f"{member.mention} non ha oggetti nell'inventario.")
        embed = discord.Embed(title=f"🎒 Inventario di {member}", color=discord.Color.green())
        for item, qty in u["inventory"].items():
            embed.add_field(name=item, value=f"x{qty}")
        await ctx.send(embed=embed)

    # ---------- SHOP ----------
    @commands.hybrid_command(name="shop", description="Mostra lo shop")
    async def shop(self, ctx):
        embed = discord.Embed(title="✨ SHOP - OFFICIAL BOXES", description="Nello shop si possono comprare:", color=discord.Color.gold())
        emojis = {"comuni": "📦", "rare": "🔷", "epiche": "💜", "mitiche": "🔥", "leggendaria": "👑"}
        for box, price in config.BOX_PRICES.items():
            embed.add_field(name=f"{emojis[box]} BOX {box.upper()}", value=f"{price} {config.CURRENCY_NAME}", inline=False)
        embed.set_footer(text="Usa /openbox <tipo> per aprire una box")
        await ctx.send(embed=embed)

    # ---------- OPENBOX ----------
    @commands.hybrid_command(name="openbox", description="Apri una box del negozio")
    @app_commands.describe(box_type="comuni/rare/epiche/mitiche/leggendaria")
    async def openbox(self, ctx, box_type: str):
        box_type = box_type.lower()
        if box_type not in config.BOX_PRICES:
            return await ctx.send("❌ Tipo di box non valido.")
        price = config.BOX_PRICES[box_type]
        econ, u = data.get_user_economy(ctx.guild.id, ctx.author.id)
        if u["balance"] < price:
            return await ctx.send("❌ Saldo insufficiente.")
        u["balance"] -= price

        boost_chance = {"comuni": 5, "rare": 10, "epiche": 15, "mitiche": 25, "leggendaria": 40}
        got_boost = random.randint(1, 100) <= boost_chance[box_type]
        reward = random.randint(price // 2, price * 2)
        u["balance"] += reward
        u["inventory"][f"Box {box_type}"] = u["inventory"].get(f"Box {box_type}", 0) + 1
        data.save("economy", econ)

        msg = f"📦 Hai aperto una Box {box_type.upper()} e ottenuto **{reward}** {config.CURRENCY_NAME}!"
        if got_boost:
            msg += "\n🚀 **BOOST ECONOMICO** ottenuto!"
        await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(Economy(bot))
