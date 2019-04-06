import os
import platform
import time
from pkg_resources import get_distribution
from psutil import Process

import discord
from discord.ext import commands
from dateutil.relativedelta import relativedelta

class Misc(commands.Cog):
    """About the bot and other things"""

    def __init__(self, bot):
        self.bot = bot

    def get_commands(self, cog):
        # WeGamersUnite :)
        for command in vars(type(cog)).values():
            if not isinstance(command, commands.Command) or command.hidden:
                continue
            yield command

    @commands.command()
    async def info(self, ctx):
        """Print some info and useful links about the bot"""

        # Sadly I couldn't break this line
        links = f'[Invite me to your server](https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=379968&scope=bot "You need manage server permission")\n\
        [Join support server](https://discord.gg/gPCwvwB "Come say hello")\n\
        [Source code](https://github.com/FrenchMasterSword/RTFMbot "Leave a ⭐")\n\
        [Report a bug](https://github.com/FrenchMasterSword/RTFMbot/issues "Open an issue")\n\
        Support by upvoting me [here](https://discordbots.org/bot/495914599531675648/vote "Thanks ^^"), [here](https://botsfordiscord.com/bots/495914599531675648/vote) and [here](https://discordbotlist.com/bots/495914599531675648/upvote)'

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

        delta = relativedelta(seconds=int(time.time() - Process(os.getpid()).create_time()))
        uptime = ''

        if delta.days: uptime += f'{int(delta.days)} d, '
        if delta.hours: uptime += f'{int(delta.hours)} h, '
        if delta.minutes: uptime += f'{int(delta.minutes)} m, '
        if delta.seconds: uptime += f'{int(delta.seconds)} s, '

        emb.add_field(name='Server count', value=str(len(self.bot.guilds)))
        emb.add_field(name='Member count', value=str(sum([guild.member_count for guild in self.bot.guilds])))

        emb.add_field(name='Python', value=f'Python {pyVersion} with {implementation}')
        emb.add_field(name='Discord.py version', value=libVersion)

        emb.add_field(name='Hosting', value=hosting)
        emb.add_field(name='Uptime', value=uptime[:-2])

        emb.add_field(name='Links', value=links, inline=False)

        await ctx.send(file=file, embed=emb)

    @commands.command()
    async def ping(self, ctx):
        """Check how the bot is doing"""

        timePing = time.monotonic()
        pinger = await ctx.send("Pinging...")
        diff = '%.2f' % (1000 * (time.monotonic() - timePing))

        emb = discord.Embed()
        emb.add_field(name="Ping", value=f'`{diff} ms`')
        emb.add_field(name="Latency", value=f'`{round(self.bot.latency*1000, 2)} ms`')

        await pinger.edit(content=None, embed=emb)

    @commands.command()
    async def help(self, ctx, specific=None):
        """Give general help or on a specific command or cog"""

        coglist = sorted([cog for cog in self.bot.cogs if cog not in ('Owner', 'ErrorHandler', 'Jishaku')])

        if not specific:
            description = f'**Prefix is `do` (space after)**\n```fix\nThere are {len(coglist)} modules```'

            lines = '\n'.join(coglist)
            cogs = f"```prolog\n{lines}```"

            emb = discord.Embed(title="RTFM help menu", colour=self.bot.config['BLUE_RTFM'],
                description=description)
            emb.add_field(name="Modules", value=cogs)
            emb.set_footer(text="Type do help <module> to see commands or do help <command>")

            return await ctx.send(embed=emb)

        if specific.capitalize() in coglist or specific.capitalize() == 'Jishaku':
            cogName = specific.capitalize()
            cog = self.bot.get_cog(cogName)
            commandsList = self.get_commands(cog)

            emb = discord.Embed(title=f"Commands from {cogName} module", colour=self.bot.config['BLUE_RTFM'],
                description=cog.__doc__)

            emb.set_footer(text="<argument needed> [optional argument] [arg a|arg b] : either a or b")

            field = []

            for command in commandsList:
                if command.hidden:
                    continue
                doc = command.short_doc
                if command.clean_params or command.aliases:
                    if command.brief:
                        signature = command.help.split('\n')[0]
                    else:
                        signature = command.signature
                    doc += f'\n**Usage -** {self.bot.config["PREFIX"]}{signature}'

                emb.add_field(name=command.name, value=doc, inline=False)

            return await ctx.send(embed=emb)

        if self.bot.get_command(specific.lower()) and not self.bot.get_command(specific.lower()).cog_name == 'Owner':
            command = self.bot.get_command(specific.lower())

            description = command.help
            if not description.startswith(command.qualified_name):
                description = f"{command.signature}\n\n{description}"

            emb = discord.Embed(title=f"Help for command {command.qualified_name}", colour=self.bot.config['BLUE_RTFM'],
                description=description)

            return await ctx.send(embed=emb)

        await ctx.send(f"No module or command named `{specific}`")


def setup(bot):
    bot.add_cog(Misc(bot))
