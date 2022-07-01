import hashlib

import discord
from discord.ext import commands

class Tools(commands.Cog):
    """Small tools to help programmers"""

    def __init__(self, bot):
        self.bot = bot
        self.algos = sorted([h for h in hashlib.algorithms_available if h.islower()])

    @commands.command()
    async def ascii(self, ctx, *, text: str):
        """Returns number representation of characters in text"""

        emb = discord.Embed(title="Unicode convert",
            description=' '.join([str(ord(letter)) for letter in text]))
        emb.set_footer(text=f'Invoked by {str(ctx.message.author)}')

        await ctx.send(embed=emb)

    @commands.command()
    async def unascii(self, ctx, *, text: str):
        """Reforms string from char codes"""

        try:
            codes = [chr(int(i)) for i in text.split(' ')]
            emb = discord.Embed(title="Unicode convert",
                description=''.join(codes))
            emb.set_footer(text=f'Invoked by {str(ctx.message.author)}')
            await ctx.send(embed=emb)
        except ValueError as e:
            await ctx.send(f"Invalid sequence. Example usage : `{self.bot.config['PREFIX']}unascii 104 101 121`")

    @commands.command()
    async def byteconvert(self, ctx, value: int, unit='Mio'):
        """Shows byte conversions of given value"""

        units = ('o', 'Kio', 'Mio', 'Gio', 'Tio', 'Pio', 'Eio', 'Zio', 'Yio')
        unit = unit.capitalize()

        if not unit in units and unit != 'O':
            return await ctx.send(f"Available units are `{'`, `'.join(units)}`.")

        emb = discord.Embed(title="Binary conversions")
        index = units.index(unit)

        for i,u in enumerate(units):
            result = round(value / 2**((i-index)*10), 14)
            emb.add_field(name=u, value=result)

        await ctx.send(embed=emb)

    @commands.command(name='hash')
    async def _hash(self, ctx, algorithm, *, text: str):
        """
        Hashes text with a given algorithm
        UTF-8, returns under hexadecimal form

        """

        algo = algorithm.lower()

        if not algo in self.algos:
            matches = '\n'.join([supported for supported in self.algos if algo in supported][:10])
            message = f"`{algorithm}` not available."
            if matches:
                message += f" Did you mean:\n{matches}"
            return await ctx.send(message)

        try:
            # Guaranteed one
            hash_object = getattr(hashlib, algo)(text.encode('utf-8'))
        except AttributeError:
            # Available
            hash_object = hashlib.new(algo, text.encode('utf-8'))

        emb = discord.Embed(title=f"{algorithm} hash",
                            description=hash_object.hexdigest())
        emb.set_footer(text=f'Invoked by {str(ctx.message.author)}')

        await ctx.send(embed=emb)


async def setup(bot):
    await bot.add_cog(Tools(bot))
