import discord
from discord.ext import commands

class Misc:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx):
        """Print some info and useful links about the bot"""

        description = "A discord bot to help you in your daily programming discord life"

        # Sadly I couldn't break this line
        links = f'[Invite me to your server](https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=108514369&scope=bot "You need manage server permission")\n\
        [Report a bug](https://github.com/FrenchMasterSword/RTFMbot/issues "Open an issue")'

        emb = discord.Embed(title="RTFM boring stuff",
            description=description)

        emb.set_thumbnail(url='http://imgur.com/a/OkVOSwf')
        emb.add_field(name='Links', value=links)

        await ctx.send(embed=emb)

def setup(bot):
    bot.add_cog(Misc(bot))