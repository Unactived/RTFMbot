import sys
import time
import traceback
import discord
from discord.ext import commands

# Mainly from
# https://github.com/IdleRPGBot/Bot/blob/4deeb4436e414327687e1621d4568b5abfbc058d/cogs/error_handler.py

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.on_command_error = self._on_command_error

    async def _on_command_error(self, ctx, error, bypass = False):
        name, content = None, None
        raised = False

        if hasattr(ctx.command, 'on_error') or (ctx.command and hasattr(ctx.cog, f'_{ctx.command.cog_name}__error')) and not bypass:
            # Do nothing if the command/cog has its own error handler and the bypass is False
            return
        if isinstance(error, commands.CommandInvokeError) and hasattr(error, 'original'):
            error = error.original
            raised = True
        if isinstance(error, commands.CommandNotFound) or isinstance(error, commands.NotOwner):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            name = "SyntaxError"
            content = f"Command `{ctx.command.name}` missing 1 required argument: `{error.param.name}`"
        elif isinstance(error, commands.BadArgument):
            name = "TypeError"
            content = str(error.args[0])
        elif isinstance(error, commands.CommandOnCooldown):
            name = "TimeoutError"
            content = f"Command on cooldown. Retry in `{format(error.retry_after, '.2f')}s`."
        elif isinstance(error, commands.CheckFailure):
            name = "PermissionError"
            content = "Escalation failed: you are not in the sudoers file.\nThis incident will be reported"
        elif isinstance(error, discord.Forbidden) or isinstance(error, discord.HTTPException):
            # We may not be able to send an embed or even send a message at this point
            bot_member = ctx.guild.get_member(self.bot.user.id)
            can_talk = ctx.channel.permissions_for(bot_member).send_messages
            if can_talk:
                return await ctx.send(f"```An error occurred while responding:\n{error.code} - {error.text}\n\nI need following permissions:\n\nEmbed links\nAttach files\nAdd reactions```")
        elif isinstance(error, UnicodeError):
            name = "UnicodeError"
            content = "The bot failed to decode your input or a command output. Make sure you only use UTF-8"

        if name is not None:
            emb = discord.Embed(title=name, description=content, colour=self.bot.config['RED'])
            await ctx.send(embed=emb)
        elif raised:
            print(f'{time.strftime("%d/%m/%y %H:%M:%S")} | {ctx.command.qualified_name}', file=sys.stderr)
            traceback.print_tb(error.__traceback__)
            print(f'{error.__class__.__name__}: {error}', file=sys.stderr, end='\n\n')
        else:
            print(traceback.format_exc())

def setup(bot):
    bot.add_cog(ErrorHandler(bot))
