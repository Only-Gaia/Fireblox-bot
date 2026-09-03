import discord
from discord.ext import commands
import data
import config
def messages_needed(level):
    # servono sempre 20 messaggi per salire di livello, qualunque sia il livello
    return 20
class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return
        levels, u = data.get_user_levels(message.guild.id, message.author.id)
        u["messages"] += 1
        needed = messages_needed(u["level"])
        if u["messages"] >= needed:
            u["messages"] -= needed
            u["level"] += 1
            data.save("levels", levels)
            await message.channel.send(
                f"🎉 {message.author.mention} è salito al livello **{u['level']}**!"
            )
            role_id = config.LEVEL_ROLES.get(u["level"])
            if role_id:
                role = message.guild.get_role(role_id)
                if role:
                    try:
                        await message.author.add_roles(role, reason="Level up")
                    except discord.Forbidden:
                        pass
        else:
            data.save("levels", levels)
    @commands.hybrid_command(name="rank", description="Mostra il tuo livello")
    async def rank(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        levels, u = data.get_user_levels(ctx.guild.id, member.id)
        needed = messages_needed(u["level"])
        mancanti = max(0, needed - u["messages"])
        embed = discord.Embed(title=f"📊 Livello di {member}", color=discord.Color.blurple())
        embed.add_field(name="Livello", value=u["level"])
        embed.add_field(name="Messaggi", value=f"{u['messages']}/{needed}")
        embed.add_field(name="Messaggi mancanti", value=mancanti)
        await ctx.send(embed=embed)
    @commands.hybrid_command(name="ranking", description="Quanto ti manca al prossimo livello")
    async def ranking(self, ctx):
        levels, u = data.get_user_levels(ctx.guild.id, ctx.author.id)
        needed = messages_needed(u["level"])
        mancanti = max(0, needed - u["messages"])
        await ctx.send(f"📈 Ti mancano **{mancanti}** messaggi per il livello {u['level'] + 1}")
    @commands.hybrid_command(name="levelleaderboard", description="Top 10 livelli del server")
    async def levelleaderboard(self, ctx):
        levels = data.load("levels").get(str(ctx.guild.id), {})
        sorted_users = sorted(levels.items(), key=lambda x: (x[1]["level"], x[1]["messages"]), reverse=True)[:10]
        embed = discord.Embed(title="🏆 Top 10 Livelli", color=discord.Color.gold())
        desc = ""
        for i, (uid, info) in enumerate(sorted_users, 1):
            member = ctx.guild.get_member(int(uid))
            name = member.mention if member else f"<@{uid}>"
            desc += f"**{i}.** {name} — Livello {info['level']}\n"
        embed.description = desc or "Nessun dato."
        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(Leveling(bot))
