import os

import discord
from discord.ext import commands

class Misc:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def info(self, ctx):
        """Print some info and useful links about the bot"""

        # Sadly I couldn't break this line
        links = f'[Invite me to your server](https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=108514369&scope=bot "You need manage server permission")\n\
        [Source code](https://github.com/FrenchMasterSword/RTFMbot "Leave a ⭐")\n\
        [Report a bug](https://github.com/FrenchMasterSword/RTFMbot/issues "Open an issue")\n\
        [Support by voting for me](https://discordbots.org/bot/495914599531675648/vote "Thanks ^^")'

        info = await self.bot.application_info()
        path = os.path.join("./RTFMbot", "icon.png")
        file = discord.File(path, "RTFM_logo.png")

        emb = discord.Embed(title=f"{info.name} card", colour=self.bot.config['BLURPLE'],
            description=info.description)

        emb.set_thumbnail(url='attachment://RTFM_logo.png')
        emb.set_footer(text= f"Coded in Python 3 by {info.owner.name}", 
            icon_url=info.owner.avatar_url)

        emb.add_field(name='Links', value=links)

        await ctx.send(file=file, embed=emb)

def setup(bot):
    bot.add_cog(Misc(bot))