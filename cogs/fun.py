import discord
from discord import app_commands
from discord.ext import commands
import random
import data

MARRIAGES_KEY = "marriages"


class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="8ball", description="Chiedi alla palla magica")
    @app_commands.describe(question="La tua domanda")
    async def eightball(self, ctx, *, question: str):
        risposte = ["Sì", "No", "Forse", "Chiedi più tardi", "Sicuramente", "Improbabile", "Assolutamente sì", "Assolutamente no"]
        await ctx.send(f"🎱 {random.choice(risposte)}")

    @commands.hybrid_command(name="say", description="Il bot ripete un messaggio")
    @commands.has_permissions(manage_messages=True)
    async def say(self, ctx, *, message: str):
        await ctx.send(message)

    @commands.hybrid_command(name="kiss", description="Bacia un utente")
    async def kiss(self, ctx, member: discord.Member):
        await ctx.send(f"💋 {ctx.author.mention} bacia {member.mention}!")

    @commands.hybrid_command(name="kill", description="Uccidi (per gioco) un utente")
    async def kill(self, ctx, member: discord.Member):
        await ctx.send(f"🔪 {ctx.author.mention} ha eliminato {member.mention}! (per finta 😄)")

    @commands.hybrid_command(name="slap", description="Schiaffeggia un utente")
    async def slap(self, ctx, member: discord.Member):
        await ctx.send(f"👋 {ctx.author.mention} schiaffeggia {member.mention}!")

    @commands.hybrid_command(name="clap", description="Applaudi un utente")
    async def clap(self, ctx, member: discord.Member):
        await ctx.send(f"👏 {ctx.author.mention} applaude {member.mention}!")

    @commands.hybrid_command(name="hug", description="Abbraccia un utente")
    async def hug(self, ctx, member: discord.Member):
        await ctx.send(f"🤗 {ctx.author.mention} abbraccia {member.mention}!")

    @commands.hybrid_command(name="marry", description="Sposa un utente")
    async def marry(self, ctx, member: discord.Member):
        marriages = data.load(MARRIAGES_KEY) if MARRIAGES_KEY in data.FILES else {}
        await ctx.send(f"💍 {ctx.author.mention} ha chiesto di sposare {member.mention}! 🎉")

    @commands.hybrid_command(name="divorce", description="Divorzia da un utente")
    async def divorce(self, ctx, member: discord.Member):
        await ctx.send(f"💔 {ctx.author.mention} ha divorziato da {member.mention}.")

    @commands.hybrid_command(name="fakenitro", description="Genera un fake nitro (per scherzo)")
    async def fakenitro(self, ctx):
        embed = discord.Embed(title="Nitro", description="Hai ricevuto un regalo!\n[Rivendica ora](https://discord.gift/fake)", color=discord.Color.blurple())
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="ship", description="Calcola la compatibilità tra due utenti")
    async def ship(self, ctx, member1: discord.Member, member2: discord.Member = None):
        member2 = member2 or ctx.author
        percentage = random.randint(0, 100)
        await ctx.send(f"💘 {member1.mention} + {member2.mention} = **{percentage}%** compatibilità!")

    @commands.hybrid_command(name="rendigay", description="Mostra quanto è gay un utente (per scherzo)")
    async def rendigay(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        percentage = random.randint(0, 100)
        await ctx.send(f"🏳️‍🌈 {member.mention} è gay al **{percentage}%**!")

    @commands.hybrid_command(name="aura", description="Calcola l'aura di un utente")
    async def aura(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        aura_points = random.randint(-1000, 1000)
        await ctx.send(f"✨ L'aura di {member.mention} è: **{aura_points}**")


async def setup(bot):
    await bot.add_cog(Fun(bot))
