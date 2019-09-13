import asyncio
import sys

import aiohttp
import discord
import json
from discord.ext import commands
from yaml import load as yaml_load

extensions = (
    'plugins.owner',
    'plugins.queries',
    'plugins.misc',
    'plugins.tools',
    'plugins.error_handler'
)

def _prefix_callable(bot, message):
    base = [f'<@!{bot.user.id}> ', f'<@{bot.user.id}> ', bot.config['PREFIX']]
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


class RTFM(commands.Bot):
    def __init__(self, config):
        super().__init__(command_prefix=_prefix_callable,
                         description=description)

        self.config = config
        self.remove_command('help')
        self.languages = ()

        with open('RTFMbot-master/default_langs.yml', 'r') as file:
            self.default = yaml_load(file)

        self.repo = "https://github.com/FrenchMasterSword/RTFMbot/"

        for extension in extensions:
            try:
                self.load_extension(extension)
            except Exception as e:
                print(f"Couldn't load the following extension : {extension} ; :{e}", file=sys.stderr)

        self.bg_task = self.loop.create_task(self.background_task())
        self.bg_dbl_count = self.loop.create_task(self.background_dbl_count())

    async def on_ready(self):
        print(f'Logged in as {self.user.name} ; ID : {self.user.id}')
        print('-------------------------------------------\n')
        await self.change_presence(status=self.config['STATUS_TYPE'],
                                   activity=discord.Game(name=self.config['STATUS']))

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
        self.bg_dbl_count.cancel()
        self.bg_task.cancel()
        await super().close()

    async def background_task(self):
        await self.wait_until_ready()

        url = 'https://tio.run/languages.json'

        while not self.is_closed():
            try:
                async with aiohttp.ClientSession() as client_session:
                    async with client_session.get(url) as response:
                        if response.status != 200:
                            print(f"Couldn't reach languages.json (status code: {response.status}).")
                            continue

                        languages = tuple(sorted(json.loads(await response.text())))

                        # Rare reassignments
                        if self.languages != languages:
                            self.languages = languages

                await asyncio.sleep(300) # 5 minutes
            except asyncio.CancelledError:
                return

    async def background_dbl_count(self):
        """POST updated stats about the self"""

        await self.wait_until_ready()

        if self.user.id != self.config['ID']:
            # Only updates if it's the true RTFM
            return

        while not self.is_closed():
            try:
                guildCount = len(self.guilds)
                usersCount = sum([guild.member_count for guild in self.guilds])
                payload = {"server_count"  : guildCount}

                url = f"https://discordbots.org/api/bots/{self.user.id}/stats"
                headers = {"Authorization" : self.config['DB_TOKEN']}

                async with aiohttp.ClientSession() as aioclient:
                    await aioclient.post(url, data=payload, headers=headers)

                url = f"https://botsfordiscord.com/api/bot/{self.user.id}"
                headers = {"Authorization" : self.config['BFD_TOKEN']}

                async with aiohttp.ClientSession() as aioclient:
                    await aioclient.post(url, data=payload, headers=headers)
                    # Only website producing 'unclosed connection' warnings
                    if not aioclient.closed():
                        await aioclient.close()

                url = f"https://discord.bots.gg/api/v1/bots/{self.user.id}/stats"
                headers = {"Authorization" : self.config['DBGG_TOKEN'], "Content-Type": "application/json"}
                payload = {"guildCount"  : guildCount}

                async with aiohttp.ClientSession() as aioclient:
                    await aioclient.post(url, data=json.dumps(payload), headers=headers)

                url = f'https://discordbotlist.com/api/bots/{self.user.id}/stats'
                headers = {"Authorization" : f"Bot {self.config['DBL_TOKEN']}", "Content-Type": "application/json"}
                payload = {"guilds"  : guildCount, "users": usersCount}

                async with aiohttp.ClientSession() as aioclient:
                    await aioclient.post(url, data=json.dumps(payload), headers=headers)

                await asyncio.sleep(300) # 5 minutes
            except asyncio.CancelledError:
                return

    def run(self, token):
        super().run(token, reconnect=True)
