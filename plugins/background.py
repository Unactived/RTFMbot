import json

import aiohttp
from discord.ext import commands, tasks

class Background(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.languages_url = 'https://tio.run/languages.json'
        self.update_languages.start()

        if bot.user.id == bot.config['ID']:
            self.lists_settings = {
                # url: headers
                f'https://discordbots.org/api/bots/{bot.config["ID"]}/stats':     {'Authorization' : bot.config['DB_TOKEN']},
                f'https://botsfordiscord.com/api/bot/{bot.config["ID"]}':         {'Authorization' : bot.config['BFD_TOKEN']},
                f'https://discord.bots.gg/api/v1/bots/{bot.config["ID"]}/stats':  {'Authorization' : bot.config['DBGG_TOKEN'], 'Content-Type': 'application/json'},
                f'https://discordbotlist.com/api/bots/{bot.config["ID"]}/stats':  {'Authorization' : f"Bot {bot.config['DBL_TOKEN']}", 'Content-Type': 'application/json'}
            }
            self.update_dbl_count.start()

    @tasks.loop(hours=1)
    async def update_languages(self):
        async with aiohttp.ClientSession() as client_session:
            async with client_session.get(self.languages_url) as response:
                if response.status != 200:
                    print(f"Couldn't reach languages.json (status code: {response.status}).")
                languages = tuple(sorted(json.loads(await response.text())))

                # Rare reassignments
                if self.bot.languages != languages:
                    self.bot.languages = languages

    @tasks.loop(hours=1)
    async def update_dbl_count(self):
        guildCount = len(self.guilds)
        usersCount = sum([guild.member_count for guild in self.guilds])

        lists_payloads = (p for p in [
            {'server_count': guildCount},
            {'server_count': guildCount},
            {'guildCount':   guildCount},
            {'guilds':       guildCount, 'users': usersCount}
        ])

        async with aiohttp.ClientSession() as aioclient:
            for url, headers in self.lists_settings:
                await aioclient.post(url, data=next(lists_payloads), headers=headers)

def setup(bot):
    bot.add_cog(Background(bot))
