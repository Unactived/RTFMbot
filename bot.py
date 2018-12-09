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
    'plugins.tools'
)

def _prefix_callable(bot, message):
    base = [f'<@!{bot.user.id}> ', f'<@{bot.user.id}> ', bot.config['PREFIX']]
    # current = utils.get_guild_attr(message.guild, 'prefix')
    # base.append(current)
    return base

description = "A discord bot to help you in your daily programming discord life"


async def update_dbl_count(bot):
    """POST updated stats about the bot"""

    guildCount = len(bot.guilds)
    usersCount = sum([guild.member_count for guild in bot.guilds])
    payload = {"server_count"  : guildCount}

    url = f"https://discordbots.org/api/bots/{bot.user.id}/stats"
    headers = {"Authorization" : bot.config['DB_TOKEN']}

    async with aiohttp.ClientSession() as aioclient:
        await aioclient.post(url, data=payload, headers=headers)

    url = f"https://botsfordiscord.com/api/bot/{bot.user.id}"
    headers = {"Authorization" : bot.config['BFD_TOKEN']}

    async with aiohttp.ClientSession() as aioclient:
        await aioclient.post(url, data=payload, headers=headers)

    url = f'https://discordbotlist.com/api/bots/{bot.user.id}/stats'
    headers = {"Authorization" : f"Bot {bot.config['DBL_TOKEN']}", "Content-Type": "application/json"}
    payload = {"guilds"  : guildCount, "users": usersCount}

    async with aiohttp.ClientSession() as aioclient:
        await aioclient.post(url, data=json.dumps(payload), headers=headers)

async def log_guilds(bot, guild, joined: bool):
    """
    Logs guilds adding/kicking the bot in the support server
    
    """
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
        with open('RTFMbot-master/languages.txt', 'r') as file:
            self.languages = tuple(file.read().split('\n'))
        with open('RTFMbot-master/default_langs.yml', 'r') as file:
            self.default = yaml_load(file)

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
        await update_dbl_count(self)

    async def on_resumed(self):
        print(f'\n[*] {self.user} resumed...')

    async def on_message(self, message):
        if type(message.channel) == discord.channel.DMChannel or message.author.bot:
            return

        await self.process_commands(message)

    async def on_guild_join(self, guild):
        await update_dbl_count(self)
        await log_guilds(self, guild, True)

    async def on_guild_remove(self, guild):
        await update_dbl_count(self)
        await log_guilds(self, guild, False)

    async def close(self):
        await super().close()

    def run(self, token):
        super().run(token, reconnect=True)
