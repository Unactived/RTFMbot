import discord
from discord.ext import commands

class Tools:
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def ascii(self, ctx, *, text: str):
        """Returns number representation of characters in text"""

        await ctx.send(','.join([str(ord(letter)) for letter in text.strip('``').strip('`')]))

    @commands.command()
    async def unascii(self, ctx, *, text: str):
        """Reforms string from char code separated with ','"""

        try:
            codes = [chr(int(i)) for i in text.strip('``').strip('`').split(',')]
            await ctx.send(''.join(codes))
        except ValueError as e:
            await ctx.send(f"Invalid sequence. Example usage : `{self.bot.config['PREFIX']}unascii 104,101,121`")

    @commands.command()
    async def byteconvert(self, ctx, value: int, unit='Mio'):
        """Shows byte convertions of given value"""

        units = ('O', 'Kio', 'Mio', 'Gio', 'Tio', 'Pio', 'Eio', 'Zio', 'Yio')
        unit = unit.capitalize()

        if not unit in units:
            return await ctx.send(f"Avaliable units are `{'`, `'.join(units)}`.")

        # value = int(value)

        emb = discord.Embed(title="Binary convertions")
        index = units.index(unit)
        
        for i,u in enumerate(units):
            result = value / 2**(i-index)
            emb.add_field(name=u, value=result)

        await ctx.send(embed=emb)

    # @commands.command()
    # async def baseconvert(self, ctx, value):
    #     """Shows base convertions of given integer value"""

    #     pass



def setup(bot):
    bot.add_cog(Tools(bot))