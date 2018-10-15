import traceback
import discord
from discord.ext import commands

class Owner:
    def __init__(self, bot):
        self.bot = bot

    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.command(aliases=['streaming', 'listening', 'watching'], hidden=True)
    async def playing(self, ctx, media=""):
        """Update bot presence accordingly to invoke command"""
        # Need URL for streaming
        if not media:
            media = f"{self.bot.config['PREFIX']}info | {self.bot.config['PREFIX']}help"
        p_types = {'playing': 0, 'streaming': 1, 'listening': 2, 'watching': 3}
        activity = discord.Activity(name=media, type=p_types[ctx.invoked_with])

        await self.bot.change_presence(activity=activity)

    @commands.command(hidden=True)
    async def load(self, ctx, *, extension):
        """Loads a cog"""
        try:
            self.bot.load_extension(f'plugins.{extension}')
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{SQUARED OK}')

    @commands.command(hidden=True)
    async def unload(self, ctx, *, extension):
        """Unloads a cog"""
        try:
            self.bot.unload_extension(f'plugins.{extension}')
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{SQUARED OK}')

    @commands.command(name='reload', hidden=True)
    async def _reload(self, ctx, *, extension):
        """Reloads a module."""
        try:
            self.bot.unload_extension(f'plugins.{extension}')
            self.bot.load_extension(f'plugins.{extension}')
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{SQUARED OK}')

    @commands.command(hidden=True)
    async def kill(self, ctx):
        """Kills process"""
        await self.bot.logout()

    @commands.guild_only()
    @commands.command(hidden=True)
    async def sayin(self, ctx, channel: discord.TextChannel, *, text: str):
        """Makes the bot say something in a given current guild's channel"""
        await channel.send(text)

    @commands.command(hidden=True)
    async def say(self, ctx, *, text: str):
        """Makes the bot say something in the current channel"""
        await ctx.send(text)

def setup(bot):
    bot.add_cog(Owner(bot))