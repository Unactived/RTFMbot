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
from discord.utils import escape_mentions

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _ref, _doc
from _used import typing, get_raw, paste
# from _tio import Tio, TioRequest
from _tio import Tio

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

    wrapping = {
        'c': '#include <stdio.h>\nint main() {code}',
        'cpp': '#include <iostream>\nint main() {code}',
        'cs': 'using System;class Program {static void Main(string[] args) {code}}',
        'java': 'public class Main {public static void main(String[] args) {code}}',
        'rust': 'fn main() {code}',
        'd': 'import std.stdio; void main(){code}'
    }

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
    async def run(self, ctx, language, *, code=''):
        """Execute code in a given programming language"""
        # Powered by tio.run

        options = {
            'stats': False,
            'wrapped': False
        }

        lang = language.strip('`').lower()
        code = code.split(' ')

        for i, option in enumerate(options):
            if f'--{option}' in code[:len(options) - i]:
                options[option] = True
                code.remove(f'--{option}')

        code = ' '.join(code)

        compilerFlags = []
        commandLineOptions = []
        args = []
        inputs = []

        lines = code.split('\n')
        code = []
        for line in lines:
            if line.startswith('input '):
                inputs.append(' '.join(line.split(' ')[1:]).strip('`'))
            elif line.startswith('compiler-flags '):
                compilerFlags.extend(line[15:].strip('`').split(' '))
            elif line.startswith('command-line-options '):
                commandLineOptions.extend(line[21:].strip('`').split(' '))
            elif line.startswith('arguments '):
                args.extend(line[10:].strip('`').split(' '))
            else:
                code.append(line)

        inputs = '\n'.join(inputs)

        code = '\n'.join(code)

        text = None

        async with ctx.typing():
            if ctx.message.attachments:
                # Code in file
                file = ctx.message.attachments[0]
                if file.size > 20000:
                    return await ctx.send("File must be smaller than 20 kio.")
                buffer = BytesIO()
                await ctx.message.attachments[0].save(buffer)
                text = buffer.read().decode('utf-8')
            elif code.split(' ')[-1].startswith('link='):
                # Code in a webpage
                base_url = urllib.parse.quote_plus(code.split(' ')[-1][5:].strip('/'), safe=';/?:@&=$,><-[]')

                url = get_raw(base_url)

                async with aiohttp.ClientSession() as client_session:
                    async with client_session.get(url) as response:
                        if response.status == 404:
                            return await ctx.send('Nothing found. Check your link')
                        elif response.status != 200:
                            return await ctx.send(f'An error occurred (status code: {response.status}). Retry later.')
                        text = await response.text()
                        if len(text) > 20000:
                            return await ctx.send('Code must be shorter than 20,000 characters.')
            elif code.strip('`'):
                # Code in message
                text = code.strip('`')
                firstLine = text.splitlines()[0]
                if re.fullmatch(r'( |[0-9A-z]*)\b', firstLine):
                    text = text[len(firstLine)+1:]

            if text is None:
                # Ensures code isn't empty after removing options
                raise commands.MissingRequiredArgument(ctx.command.clean_params['code'])

            # common identifiers, also used in highlight.js and thus discord codeblocks
            quickmap = {
                'asm': 'assembly',
                'c#': 'cs',
                'c++': 'cpp',
                'csharp': 'cs',
                'f#': 'fs',
                'fsharp': 'fs',
                'js': 'javascript',
                'nimrod': 'nim',
                'py': 'python',
                'q#': 'qs',
                'rs': 'rust',
                'sh': 'bash',
            }

            if lang in quickmap:
                lang = quickmap[lang]

            if lang in self.bot.default:
                lang = self.bot.default[lang]
            if not lang in self.bot.languages:
                matches = '\n'.join([language for language in self.bot.languages if lang in language][:10])
                lang = escape_mentions(lang)
                message = f"`{lang}` not available."
                if matches:
                    message = message + f" Did you mean:\n{matches}"

                return await ctx.send(message)

            if options['wrapped']:
                if not (any(map(lambda x: lang.split('-')[0] == x, self.wrapping))) or lang in ('cs-mono-shell', 'cs-csi'):
                    return await ctx.send(f'`{lang}` cannot be wrapped')

                for beginning in self.wrapping:
                    if lang.split('-')[0] == beginning:
                        text = self.wrapping[beginning].replace('code', text)
                        break

            tio = Tio(lang, text, compilerFlags=compilerFlags, inputs=inputs, commandLineOptions=commandLineOptions, args=args)

            result = await tio.send()

            if not options['stats']:
                try:
                    start = result.rindex("Real time: ")
                    end = result.rindex("%\nExit code: ")
                    result = result[:start] + result[end+2:]
                except ValueError:
                    # Too much output removes this markers
                    pass

            if len(result) > 1991 or result.count('\n') > 40:
                # If it exceeds 2000 characters (Discord longest message), counting ` and ph\n characters
                # Or if it floods with more than 40 lines
                # Create a hastebin and send it back
                link = await paste(result)

                if link is None:
                    return await ctx.send("Your output was too long, but I couldn't make an online bin out of it")
                return await ctx.send(f'Output was too long (more than 2000 characters or 40 lines) so I put it here: {link}')

            zero = '\N{zero width space}'
            result = re.sub('```', f'{zero}`{zero}`{zero}`{zero}', result)

            # ph, as placeholder, prevents Discord from taking the first line
            # as a language identifier for markdown and remove it
            returned = await ctx.send(f'```ph\n{result}```')

        await returned.add_reaction('🗑')
        returnedID = returned.id

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == '🗑' and reaction.message.id == returnedID

        try:
            await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            pass
        else:
            await returned.delete()


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

        async with aiohttp.ClientSession() as client_session:
            async with client_session.get(url) as response:
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
            "wrapped argument": self.wrapping,
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


def setup(bot):
    bot.add_cog(Coding(bot))

