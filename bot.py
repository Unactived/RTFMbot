import asyncio
import sys

import discord
import json
from discord.ext import commands
from yaml import safe_load as yaml_load

extensions = (
    'plugins.owner',
    'plugins.queries',
    'plugins.misc',
    'plugins.tools',
    'plugins.error_handler'
)

def _prefix_callable(bot, message):
    base = [bot.user.mention, bot.config['PREFIX']]
    # current = utils.get_guild_attr(message.guild, 'prefix')
    # base.append(current)
    return base

description = "A discord bot to help you in your daily programming discord life"

async def log_guilds(bot, guild, joined: bool):
    """
    Logs guilds adding/kicking the bot in the support server

    """
    if bot.user.id != bot.config['ID']:
        # true RTFM
        return
    logsChannel = bot.get_channel(bot.config['SUPPORT_LOG_CHANNEL_ID'])
    if joined:
        content = 'added RTFM to their community ! :smiley:'
    else:
        content = 'removed RTFM from their community :pensive:'

    emb = discord.Embed(description=f"{guild.name} {content}")
    emb.set_thumbnail(url=guild.icon_url)

    await logsChannel.send(embed=emb)


class RTFM(commands.AutoShardedBot):
    def __init__(self, config):
        super().__init__(command_prefix=_prefix_callable,
                         description=description)

        self.config = config
        self.remove_command('help')
        self.languages = ()

        with open('default_langs.yml', 'r') as file:
            self.default = yaml_load(file)

        self.repo = "https://github.com/FrenchMasterSword/RTFMbot/"

        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f"Couldn't load the following extension : {extension} ; :{e}", file=sys.stderr)

    async def on_ready(self):
        print(f'Logged in as {self.user.name} ; ID : {self.user.id}')
        print('-------------------------------------------\n')
        await self.change_presence(status=self.config['STATUS_TYPE'],
                                   activity=discord.Game(name=self.config['STATUS']))
        self.load_extension('plugins.background')

    async def on_resumed(self):
        print(f'\n[*] {self.user} resumed...')

    async def on_message(self, message):
        if type(message.channel) == discord.channel.DMChannel or message.author.bot:
            return

        await self.process_commands(message)

    async def on_guild_join(self, guild):
        await log_guilds(self, guild, True)

    async def on_guild_remove(self, guild):
        await log_guilds(self, guild, False)

    async def close(self):
        await super().close()

    def run(self, token):
        super().run(token, reconnect=True)
