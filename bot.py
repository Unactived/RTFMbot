import asyncio
import sys
import traceback

import discord
import aiohttp
import json
from discord.ext import commands

extensions = (
    'plugins.owner',
    'plugins.queries',
    'plugins.misc',
    'plugins.tools',
    'plugins.manage',
    'plugins.error_handler'
)

def _prefix_callable(bot, message):
    base = [f'<@!{bot.user.id}> ', f'<@{bot.user.id}> ', f'<@!{bot.user.id}>', f'<@{bot.user.id}>']
    base.append(bot.prefixes.get(message.guild.id) or bot.config['PREFIX'])

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
    def __init__(self, config, db):
        allowed_mentions = discord.AllowedMentions(roles=False, everyone=False, replied_user=False)

        intents = discord.Intents(
            guilds=True,
            members=False, # don't have it anyway
            bans=False,
            voice_states=False,
            messages=True,
            message_content=False,
            integrations=True
        )

        self.config = config

        super().__init__(
            command_prefix=_prefix_callable,
            description=description,
            allowed_mentions=allowed_mentions,
            activity=discord.Game(name=self.config['STATUS']),
            status=self.config['STATUS_TYPE'],
            intents=intents
        )

        self.db = db

        self.remove_command('help')

        with open('languages.txt', 'r') as file:
            self.languages = set(file.read().split('\n'))

        self.repo = "https://github.com/Unactived/RTFMbot/"

    async def on_ready(self):
        print(f'Logged in as {self.user.name} ; ID : {self.user.id}')
        print('-------------------------------------------\n')

    async def setup_hook(self):
        """Start things after the first bot's login if they need it, like tasks"""

        G,U = await self.db.init()

        self.blacklist = {u['id'] for u in U if u['blacklisted']}
        self.blacklist.update({g['id'] for g in G  if g['blacklisted']})

        self.prefixes = {g['id']: g['prefix'][:-1] for g in G} # see manage


        for extension in extensions:
            try:
                await self.load_extension(extension)
            except:
                print(f"Couldn't load the following extension : {extension} ; :\n{traceback.format_exc()}", file=sys.stderr)

        # # DEVELOPMENT
        # self.tree.copy_global_to(guild=discord.Object(id=380357709813252096))

        await self.load_extension('plugins.background')

    async def on_resumed(self):
        print(f'\n[*] {self.user} resumed...')

    async def on_message(self, message):
        # Disable DMs, don't answer bots, ignore blacklisteds
        if message.guild is None or message.author.bot or message.author.id in self.blacklist:
            return

        await self.process_commands(message)

    async def on_guild_join(self, guild):
        if guild.id in self.blacklist:
            return await guild.leave()

        await log_guilds(self, guild, True)

    async def on_guild_remove(self, guild):
        # don't log departures from blacklisting
        if not guild.id in self.blacklist:
            await log_guilds(self, guild, False)

    async def close(self):
        await super().close()

#    def run(self, token):
#        super().run(token, reconnect=True)
