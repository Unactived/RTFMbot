import json

from discord.ext import commands, tasks

class Background(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.languages_url = 'https://tio.run/languages.json'
        self.update_languages.start()

        if bot.user.id == bot.config['ID']: # actual RTFM
            self.lists_settings = (
                # url: headers
                (f'https://top.gg/api/bots/{bot.config["ID"]}/stats',                 {'Authorization' : bot.config['DB_TOKEN']}),
                (f'https://discords.com/bots/api/bot/{bot.config["ID"]}',             {'Authorization' : bot.config['BFD_TOKEN']}),
                (f'https://discord.bots.gg/api/v1/bots/{bot.config["ID"]}/stats',     {'Authorization' : bot.config['DBGG_TOKEN']}),
                (f'https://discordbotlist.com/api/v1/bots/{bot.config["ID"]}/stats',  {'Authorization' : bot.config['DBL_TOKEN']})
            )
            self.update_dbl_count.start()

    @tasks.loop(hours=1.0)
    async def update_languages(self):
        async with self.bot.session.get(self.languages_url) as response:
            if response.status != 200:
                print(f"Couldn't reach languages.json (status code: {response.status}).")
            languages = set(json.loads(await response.text()))

            # Rare reassignments
            if self.bot.languages != languages:
                self.bot.languages = languages

    @tasks.loop(minutes=30.0)
    async def update_dbl_count(self):
        # grouped to avoid doing it ~4 times and maintain same stats among websites
        guildCount = len(self.bot.guilds)
        shardCount = self.bot.shard_count

        lists_payloads = (p for p in [
            {'server_count': guildCount, 'shard_count': shardCount},
            {'server_count': guildCount},
            {'guildCount':   guildCount, "shardCount": shardCount},
            {'guilds':       guildCount}
        ])

        for url, headers in self.lists_settings:
            await self.bot.session.post(url, data=next(lists_payloads), headers=headers)

async def setup(bot):
    await bot.add_cog(Background(bot))
