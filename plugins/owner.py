import io
import os
import textwrap
import traceback
from contextlib import redirect_stdout
from yaml import load as yaml_load
from yaml import dump as yaml_dump

import discord
from discord.ext import commands

class Owner:
    def __init__(self, bot):
        self.bot = bot
        self._last_eval_result = None

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

def setup(bot):
    bot.add_cog(Owner(bot))
