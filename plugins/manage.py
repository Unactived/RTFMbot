import discord
from discord.ext import commands

class Manage(commands.Cog):
    """Manage the bot for your server. Requires `Manage server` permission."""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True

        # if ctx.guild is None:
        #     return True

        return ctx.author.guild_permissions.manage_guild

    @commands.command()
    async def setprefix(self, ctx, new_prefix):
        """
        Set the new bot's prefix. Use quotes to include spaces.
        e.g. `do setprefix "do "`

        Since Discord trims leading whitespace in messages, leading whitespace isn't allowed.
        Max allowed length is 128 characters.

        If you ever mess up or forget somehow, remember that the bot's mention, followed by exactly one space, is always a valid prefix.

        """

        if not new_prefix:
            raise commands.BadArgument("Prefix cannot be an empty string.")

        if len(new_prefix) > 128:
            raise commands.BadArgument("Prefix cannot be longer than 128 characters.")

        if new_prefix.lstrip() != new_prefix:
            raise commands.BadArgument("Leading whitespace isn't allowed.")

        self.bot.prefixes[ctx.guild.id] = new_prefix

        await self.bot.db.set_in_guild(ctx.guild.id, 'prefix', new_prefix+'.') # we add a non-whitespace char so Postgres doesn't trim

        await ctx.send(f'Prefix set to "{new_prefix}"')


async def setup(bot):
    await bot.add_cog(Manage(bot))
