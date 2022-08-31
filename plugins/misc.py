import os
import platform
import time
from pkg_resources import get_distribution
from psutil import Process
from typing import Optional

import discord
from discord.ext import commands
from dateutil.relativedelta import relativedelta

hidden_cogs = ('Owner', 'ErrorHandler', 'Background', 'Jishaku')



class Help(commands.HelpCommand):
    """The bot's help command"""

    BLUE_RTFM = 0x1EDBF8

    async def slash_command_callback(self, ctx: discord.Interaction, /, *, command_or_module: Optional[str] = None) -> None:
        """Turn interactions into contexts so past implementations work, akin to hybrid commands"""

        ctx = await commands.Context.from_interaction(ctx)
        self.context = ctx

        await self.command_callback(ctx, command=command_or_module)

    def get_destination(self) -> discord.abc.Messageable:
        # Return context so .reply() works on both Messageable regular and interaction-based contexts

        return self.context

    async def command_not_found(self, string):
        return f'No command or cog named "{string}" found. Remember names are case-sensitive.'

    async def send_bot_help(self, mapping):
        mapping.pop(None)
        coglist = sorted([cog.qualified_name for cog in mapping if cog.qualified_name not in hidden_cogs])

        description = f'**Prefix is `/` or the bot\'s mention**\n```fix\nThere are {len(coglist)} modules```'
        lines = '\n'.join(coglist)
        cogs = f"```prolog\n{lines}```"

        emb = discord.Embed(title="RTFM help menu (online version)", colour=self.BLUE_RTFM, description=description,
                url=f'{self.cog.bot.repo}wiki')
        emb.add_field(name="Modules", value=cogs)
        emb.set_footer(text="Type do help <module> to see commands or do help <command>")

        await self.get_destination().reply(embed=emb)

    async def send_cog_help(self, cog):
        if cog.qualified_name in hidden_cogs:
            return await self.get_destination().reply(f'No command or cog called "{cog.qualified_name}" found. Remember names are case-sensitive.')
        commandsList = await self.filter_commands(cog.get_commands())

        emb = discord.Embed(title=f"Commands from {cog.qualified_name} module (online version)", colour=self.BLUE_RTFM,
            description=cog.__doc__, url=f'{self.cog.bot.repo}wiki/{cog.qualified_name}-module')

        emb.set_footer(text="<argument needed> [optional argument] [a|b] : either a or b")

        for command in commandsList:
            doc = command.short_doc
            if command.clean_params or command.aliases:
                if command.brief:
                    signature = command.help.split('\n')[0]
                else:
                    signature = f'{command.qualified_name} {command.signature}'
                doc += f'\n**Usage -** /{signature}'

            emb.add_field(name=command.name, value=doc, inline=False)

        await self.get_destination().reply(embed=emb)

    async def send_command_help(self, command):
        # We partake in a mild amount of tomfoolery
        if command.hidden or command.cog.qualified_name in hidden_cogs:
            return await self.get_destination().reply(f'No command or cog called "{command.qualified_name}" found. Remember names are case-sensitive.')

        description = command.help
        if not description.startswith(command.qualified_name):
            description = f"{command.qualified_name} {command.signature}\n\n{description}"

        emb = discord.Embed(title=f"Help for command {command.qualified_name} (online version)", colour=self.BLUE_RTFM,
        description=description, url=f'{self.cog.bot.repo}wiki/{command.cog.qualified_name}-module#{command.qualified_name}')

        await self.get_destination().reply(embed=emb)

class Misc(commands.Cog):
    """About the bot and other things"""

    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = Help()
        bot.help_command.cog = self

        # https://github.com/Rapptz/discord.py/blob/master/discord/app_commands/commands.py#L1579
        bot.app_help_command = discord.app_commands.Command(
            name="help",
            description=bot.help_command.__doc__,
            callback=bot.help_command.slash_command_callback,
            parent=None,
            nsfw=False,
            extras={},
        )

        self.bot.tree.add_command(self.bot.app_help_command)

    async def cog_unload(self):
        # To keep a minimal help
        self.bot.help_command = self._original_help_command

    @commands.hybrid_command()
    async def info(self, ctx):
        """Print some info and useful links about the bot"""

        # Sadly I couldn't break this line
        links = f'[Invite me to your server](https://discordapp.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=379968&scope=bot "You need manage server permission")\n\
        [Join support server](https://discord.gg/gPCwvwB "Come say hello")\n\
        [Source code]({self.bot.repo} "Leave a ⭐")\n\
        [Report a bug]({self.bot.repo}issues "Open an issue")\n\
        Support by upvoting me [here](https://discordbots.org/bot/495914599531675648/vote "Thanks ^^"), [here](https://botsfordiscord.com/bots/495914599531675648/vote) and [here](https://discordbotlist.com/bots/495914599531675648/upvote)'

        info = await self.bot.application_info()
        file = discord.File("icon.png", "RTFM_logo.png")

        emb = discord.Embed(title=f"{info.name} card", colour=self.bot.config['BLURPLE'],
            description=info.description)

        emb.set_thumbnail(url='attachment://RTFM_logo.png')
        emb.set_footer(text= f"Coded in Python 3 by {info.owner.name}", 
            icon_url=info.owner.avatar.url)

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

        hashes = os.popen('git log --oneline -3 --pretty=format:"%h"').read().split('\n')

        changes = '\n'.join([f'[`{h}`]({self.bot.repo}commit/{h})' for h in hashes])

        emb.add_field(name='Servers', value=str(len(self.bot.guilds)))
        emb.add_field(name='Uptime', value=uptime[:-2])
        emb.add_field(name='Latest changes', value=changes)

        #emb.add_field(name='Member count', value=str(sum([guild.member_count for guild in self.bot.guilds])))

        emb.add_field(name='Python', value=f'Python {pyVersion} with {implementation}')
        emb.add_field(name='Discord.py version', value=libVersion)
        emb.add_field(name='Hosting', value=hosting)

        emb.add_field(name='Links', value=links, inline=False)

        await ctx.reply(file=file, embed=emb)

    @commands.hybrid_command()
    async def ping(self, ctx: commands.Context):
        """Check how the bot is doing"""

        timePing = time.monotonic()
        pinger = await ctx.reply("Pinging...")
        diff = '%.2f' % (1000 * (time.monotonic() - timePing))

        emb = discord.Embed()
        emb.add_field(name="Ping", value=f'`{diff} ms`')
        emb.add_field(name="Latency", value=f'`{round(self.bot.latency*1000, 2)} ms`')

        await pinger.edit(content=None, embed=emb)

async def setup(bot):
    await bot.add_cog(Misc(bot))
