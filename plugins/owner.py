import io
import os
import textwrap
import traceback
import typing
from contextlib import redirect_stdout
from yaml import safe_load as yaml_load
from yaml import dump as yaml_dump

import discord
from discord.ext import commands

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_eval_result = None

    async def cog_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @commands.group(invoke_without_command=True, hidden=True)
    async def blacklist(self, ctx, to_blacklist: typing.Union[discord.User, discord.Guild, None]):
        """Blacklist a user or server from using the bot."""

        if to_blacklist is None:
            return await ctx.send("Could not determine target.")

        self.bot.blacklist.add(to_blacklist.id)

        if isinstance(to_blacklist, (discord.User, discord.Member)):
            await self.bot.db.set_in_user(to_blacklist.id, 'blacklisted', True)
            return await ctx.send(f"Blacklisted user {str(to_blacklist)}.")

        await self.bot.db.set_in_guild(to_blacklist.id, 'blacklisted', True)
        await ctx.send(f"Blacklisted server {str(to_blacklist)}. Leaving.")

        return await to_blacklist.leave()

    @blacklist.command(hidden=True)
    async def remove(self, ctx, to_remove: typing.Union[discord.User, int]):
        """Remove a user or server from the bot's blacklist."""

        # We cannot convert (typehint) to a discord.Guild
        # since the bot leaves blacklisted guilds

        if isinstance(to_remove, (discord.User, discord.Member)):
            id = to_remove.id
            prefix = f'{str(to_remove)}, '
        else:
            id = to_remove
            prefix = ''


        if not id in self.bot.blacklist:
            return await ctx.send(prefix + f'ID: {id} not in blacklist.')

        self.bot.blacklist.remove(id)

        if prefix:
            await self.bot.db.set_in_user(id, 'blacklisted', False)
            return await ctx.send(prefix + f'removed from blacklist.')

        # We need to determine if the integer obtained is the id of a guild or a user we no longer see

        is_user = await self.bot.db.get_from_user(id, 'id') # an int or None

        if is_user:
            await self.bot.db.set_in_user(id, 'blacklisted', False)
            return await ctx.send(f'User with ID: {id} removed from blacklist.')

        await self.bot.db.set_in_guild(id, 'blacklisted', False)
        return await ctx.send(f'Server with ID: {id} removed from blacklist.')

    @commands.command(aliases=['streaming', 'listening', 'watching'], hidden=True)
    async def playing(self, ctx, media=""):
        """Update bot presence accordingly to invoke command"""
        # Need URL for streaming
        if not media:
            media = f"{self.bot.config['PREFIX']}info | {self.bot.config['PREFIX']}help"
        p_types = {'playing': 0, 'streaming': 1, 'listening': 2, 'watching': 3}
        activity = discord.Activity(name=media, type=p_types[ctx.invoked_with])

        # Keep trace of it

        with open('config.yml', 'r') as file:
            stuff = yaml_load(file)

        stuff['STATUS_TYPE'] = p_types[ctx.invoked_with]
        stuff['STATUS'] = media

        with open('config.yml', 'w') as file:
            yaml_dump(stuff, file)

        self.bot.config = stuff

        await self.bot.change_presence(activity=activity)

    @commands.command(hidden=True)
    async def load(self, ctx, *, extension):
        """Loads a cog"""
        try:
            await self.bot.load_extension(f'plugins.{extension}')
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{SQUARED OK}')

    @commands.command(hidden=True)
    async def unload(self, ctx, *, extension):
        """Unloads a cog"""
        try:
            await self.bot.unload_extension(f'plugins.{extension}')
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{SQUARED OK}')

    @commands.command(name='reload', hidden=True)
    async def _reload(self, ctx, *, extension):
        """Reloads a module."""
        try:
            await self.bot.unload_extension(f'plugins.{extension}')
            await self.bot.load_extension(f'plugins.{extension}')
        except Exception:
            await ctx.send(f'```py\n{traceback.format_exc()}\n```')
        else:
            await ctx.send('\N{SQUARED OK}')

    @commands.command(hidden=True)
    async def kill(self, ctx):
        """Kills process"""
        await self.bot.logout()

    @commands.command(hidden=True)
    async def cogupdate(self, ctx):
        """Fetches and update cogs from github repo"""
        os.system(f'./cogupdate.sh')

    @commands.command(hidden=True)
    async def restart(self, ctx):
        """Restarts bot"""
        await self.bot.logout()
        os.system("python3.6 RTFMbot/launcher.py")

    @commands.guild_only()
    @commands.command(hidden=True)
    async def sayin(self, ctx, channel: discord.TextChannel, *, text: str):
        """Makes the bot say something in a given current guild's channel"""
        await channel.send(text)

    @commands.command(hidden=True)
    async def say(self, ctx, *, text: str):
        """Makes the bot say something in the current channel"""
        try:
            await ctx.message.delete()
        except commands.errors.CommandInvokeError:
            pass
        await ctx.send(text)

    def _clean_code(self, code):
        # Markdown py ; not python
        if code.startswith('```') and code.endswith('```'):
            return '\n'.join(code.split('\n')[1:-1])
        return code.strip('`\n')

    @commands.is_owner()
    @commands.command(name='eval', hidden=True)
    async def _eval(self, ctx, *, code: str):
        """Eval some code"""

        env = {
            'bot': self.bot,
            'ctx': ctx,
            'guild': ctx.guild,
            'channel': ctx.channel,
            'author': ctx.author,
            'message': ctx.message,
            '_': self._last_eval_result
        }
        env.update(globals())

        code = self._clean_code(code)
        buffer = io.StringIO()

        # function placeholder
        to_compile = f'async def foo():\n{textwrap.indent(code, " ")}'

        try:
            exec(to_compile, env)
        except Exception as e:
            return await ctx.send(f'```py\n{e.__class__.__name__}: {e}\n``')

        foo = env['foo']
        try:
            with redirect_stdout(buffer):
                ret = await foo()
        except Exception:
            value = buffer.getvalue()
            await ctx.send(f'```py\n{value}{traceback.format_exc()}\n```')
        else:
            value = buffer.getvalue()
            try:
                await ctx.message.add_reaction('\N{INCOMING ENVELOPE}')
            except Exception:
                # well...
                pass

            if ret is None:
                if value is not None:
                    await ctx.send(f'```py\n{value}\n```')
                else:
                    self._last_result = ret
                    await ctx.send(f'```py\n{value}{ret}\n```')

async def setup(bot):
    await bot.add_cog(Owner(bot))
