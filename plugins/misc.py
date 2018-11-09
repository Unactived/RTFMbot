import os
import platform
from pkg_resources import get_distribution
from time import perf_counter

import discord
from discord.ext import commands
from dateutil.relativedelta import relativedelta

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
        path = os.path.join("./RTFMbot-master", "icon.png")
        file = discord.File(path, "RTFM_logo.png")

        emb = discord.Embed(title=f"{info.name} card", colour=self.bot.config['BLURPLE'],
            description=info.description)

        emb.set_thumbnail(url='attachment://RTFM_logo.png')
        emb.set_footer(text= f"Coded in Python 3 by {info.owner.name}", 
            icon_url=info.owner.avatar_url)

        implementation = platform.python_implementation()
        pyVersion = platform.python_version()
        libVersion = get_distribution("discord.py").version
        hosting = platform.platform()

        delta = relativedelta(seconds=perf_counter())
        uptime = ''

        if delta.days: uptime += f'{int(delta.days)} days, '
        if delta.hours: uptime += f'{int(delta.hours)} hours, '
        if delta.minutes: uptime += f'{int(delta.minutes)} minutes, '
        if delta.seconds: uptime += f'{int(delta.seconds)} seconds, '

        emb.add_field(name='Server count', value=str(len(self.bot.guilds)))
        emb.add_field(name='Member count', value=str(sum([guild.member_count for guild in self.bot.guilds])))

        emb.add_field(name='Python', value=f'Python {pyVersion} with {implementation}')
        emb.add_field(name='Discord.py version', value=libVersion)

        emb.add_field(name='Hosting', value=hosting)
        emb.add_field(name='Uptime', value=uptime[:-2])

        emb.add_field(name='Links', value=links, inline=False)

        await ctx.send(file=file, embed=emb)

def setup(bot):
    bot.add_cog(Misc(bot))