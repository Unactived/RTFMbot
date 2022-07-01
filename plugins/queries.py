import asyncio
import os
import re
import sys
import urllib.parse
from io import BytesIO
from hashlib import algorithms_available as algorithms

import aiohttp
import discord
import stackexchange as se
# from pytio import Tio, TioRequest
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
# from discord.utils import escape_mentions

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _ref, _doc
from _used import typing, get_raw, paste, Refresh, wrapping, prepare_payload, execute_run
# from _tio import Tio, TioRequest

class Coding(commands.Cog):
    """To test code and check docs"""

    def __init__(self, bot):
        self.bot = bot

    def get_content(self, tag):
        """Returns content between two h2 tags"""

        bssiblings = tag.next_siblings
        siblings = []
        for elem in bssiblings:
            # get only tag elements, before the next h2
            # Putting away the comments, we know there's
            # at least one after it.
            if type(elem) == NavigableString:
                continue
            # It's a tag
            if elem.name == 'h2':
                break
            siblings.append(elem.text)
        content = '\n'.join(siblings)
        if len(content) >= 1024:
            content = content[:1021] + '...'

        return content

    referred = {
        "csp-directives": _ref.csp_directives,
        "git": _ref.git_ref,
        "git-guides": _ref.git_tutorial_ref,
        "haskell": _ref.haskell_ref,
        "html5": _ref.html_ref,
        "http-headers": _ref.http_headers,
        "http-methods": _ref.http_methods,
        "http-status-codes": _ref.http_status,
        "sql": _ref.sql_ref
    }

    # TODO: lua, java, javascript, asm
    documented = {
        'c': _doc.c_doc,
        'cpp': _doc.cpp_doc,
        'haskell': _doc.haskell_doc,
        'python': _doc.python_doc
    }

    @commands.command(
help='''run <language> [--wrapped] [--stats] <code>

for command-line-options, compiler-flags and arguments you may
add a line starting with this argument, and after a space add
your options, flags or args.

stats option displays more informations on execution consumption
wrapped allows you to not put main function in some languages, which you can see in `list wrapped argument`

<code> may be normal code, but also an attached file, or a link from [hastebin](https://hastebin.com) or [Github gist](https://gist.github.com)
If you use a link, your command must end with this syntax:
`link=<link>` (no space around `=`)
for instance : `do run python link=https://hastebin.com/resopedahe.py`
The link may be the raw version, and with/without the file extension

If the output exceeds 40 lines or Discord max message length, it will be put
in a new hastebin and the link will be returned.

When the code returns your output, you may delete it by clicking :wastebasket: in the following minute.
Useful to hide your syntax fails or when you forgot to print the result.''',
brief='Execute code in a given programming language'
        )
    async def run(self, ctx, *, payload=''):
        """Execute code in a given programming language"""

        if not payload:
            emb = discord.Embed(title='SyntaxError',description=f"Command `run` missing a required argument: `language`",colour=0xff0000)
            return await ctx.send(embed=emb)

        no_rerun = True
        language = payload
        lang = None # to override in 2 first cases

        if ctx.message.attachments:
            # Code in file
            file = ctx.message.attachments[0]
            if file.size > 20000:
                return await ctx.send("File must be smaller than 20 kio.")
            buffer = BytesIO()
            await ctx.message.attachments[0].save(buffer)
            text = buffer.read().decode('utf-8')
            lang = re.split(r'\s+', payload, maxsplit=1)[0]
        elif payload.split(' ')[-1].startswith('link='):
            # Code in a webpage
            base_url = urllib.parse.quote_plus(payload.split(' ')[-1][5:].strip('/'), safe=';/?:@&=$,><-[]')

            url = get_raw(base_url)

            async with self.bot.session.get(url) as response:
                if response.status == 404:
                    return await ctx.send('Nothing found. Check your link')
                elif response.status != 200:
                    return await ctx.send(f'An error occurred (status code: {response.status}). Retry later.')
                text = await response.text()
                if len(text) > 20000:
                    return await ctx.send('Code must be shorter than 20,000 characters.')
                lang = re.split(r'\s+', payload, maxsplit=1)[0]
        else:
            no_rerun = False

            language,text,errored = prepare_payload(payload) # we call it text but it's an embed if it errored #JustDynamicTypingThings

            if errored:
                return await ctx.send(embed=text)

        async with ctx.typing():
            if lang:
                language = lang


            output = await execute_run(self.bot, language, text)

            view = Refresh(self.bot, no_rerun)

            try:
                returned = await ctx.reply(output, view=view)
                buttons = True
            except discord.HTTPException: # message deleted
                returned = await ctx.send(output, view=view)
                buttons = False

        if buttons:

            await view.wait()

            try:
                await returned.edit(view=None)
                view.stop()
            except:
                # We deleted the message
                pass

    @commands.command(aliases=['ref'])
    @typing
    async def reference(self, ctx, language, *, query: str):
        """Returns element reference from given language"""

        lang = language.strip('`')

        if not lang.lower() in self.referred:
            return await ctx.send(f"{lang} not available. See `{self.bot.config['PREFIX']}list references` for available ones.")

        await self.referred[lang.lower()](ctx, query.strip('`'))

    @commands.command(aliases=['doc'])
    @typing
    async def documentation(self, ctx, language, *, query: str):
        """Returns element reference from given language"""

        lang = language.strip('`')

        if not lang.lower() in self.documented:
            return await ctx.send(f"{lang} not available. See `{self.bot.config['PREFIX']}list documentations` for available ones.")

        await self.documented[lang.lower()](ctx, query.strip('`'))

    @commands.command()
    @typing
    async def man(self, ctx, *, page: str):
        """Returns the manual's page for a (mostly Debian) linux command"""

        base_url = f'https://man.cx/{page}'
        url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

        async with self.bot.session.get(url) as response:
            if response.status != 200:
                return await ctx.send('An error occurred (status code: {response.status}). Retry later.')

            soup = BeautifulSoup(await response.text(), 'lxml')

            nameTag = soup.find('h2', string='NAME\n')

            if not nameTag:
                # No NAME, no page
                return await ctx.send(f'No manual entry for `{page}`. (Debian)')

            # Get the two (or less) first parts from the nav aside
            # The first one is NAME, we already have it in nameTag
            contents = soup.find_all('nav', limit=2)[1].find_all('li', limit=3)[1:]

            if contents[-1].string == 'COMMENTS':
                contents.remove(-1)

            title = self.get_content(nameTag)

            emb = discord.Embed(title=title, url=f'https://man.cx/{page}')
            emb.set_author(name='Debian Linux man pages')
            emb.set_thumbnail(url='https://www.debian.org/logos/openlogo-nd-100.png')

            for tag in contents:
                h2 = tuple(soup.find(attrs={'name': tuple(tag.children)[0].get('href')[1:]}).parents)[0]
                emb.add_field(name=tag.string, value=self.get_content(h2))

            await ctx.send(embed=emb)

    @commands.cooldown(1, 8, BucketType.user)
    @commands.command(aliases=['se'])
    @typing
    async def stack(self, ctx, siteName, *, query: str):
        """Queries given StackExchange website and gives you top results. siteName is case-sensitive."""

        if siteName[0].islower() or not siteName in dir(se):
            await ctx.send(f"{siteName} does not appear to be in the StackExchange network."
                " Check the case and the spelling.")

        site = se.Site(getattr(se, siteName), self.bot.config['SE_KEY'])
        site.impose_throttling = True
        site.throttle_stop = False

        qs = site.search(intitle=query)[:3]
        if qs:
            emb = discord.Embed(title=query)
            emb.set_thumbnail(url=f'http://s2.googleusercontent.com/s2/favicons?domain_url={site.domain}')
            emb.set_footer(text="Hover for vote stats")

            for q in qs:
                # Fetch question's data, include vote_counts and answers
                q = site.question(q.id, filter="!b1MME4lS1P-8fK")
                emb.add_field(name=f"`{len(q.answers)} answers` Score : {q.score}",
                              value=f'[{q.title}](https://{site.domain}/q/{q.id}'
                                    f' "{q.up_vote_count}🔺|{q.down_vote_count}🔻")',
                              inline=False)

            await ctx.send(embed=emb)
        else:
            await ctx.send("No results")

    @commands.command()
    async def list(self, ctx, *, group=None):
        """Lists available choices for other commands"""

        choices = {
            "documentations": self.documented,
            "hashing": sorted([h for h in algorithms if h.islower()]),
            "references": self.referred,
            "wrapped argument": wrapping,
        }

        if group == 'languages':
            emb = discord.Embed(title=f"Available for {group}: {len(self.bot.languages)}",
                description=f'View them on [tio.run](https://tio.run/#), or in [JSON format](https://tio.run/languages.json)')
            return await ctx.send(embed=emb)

        if not group in choices:
            emb = discord.Embed(title="Available listed commands", description=f"`languages`, `{'`, `'.join(choices)}`")
            return await ctx.send(embed=emb)

        availables = choices[group]
        description=f"`{'`, `'.join([*availables])}`"
        emb = discord.Embed(title=f"Available for {group}: {len(availables)}", description=description)
        await ctx.send(embed=emb)


async def setup(bot):
    await bot.add_cog(Coding(bot))

