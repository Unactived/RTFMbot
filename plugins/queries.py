import os
import re
import sys
import urllib.parse

import aiohttp
import discord
import stackexchange as se
# from pytio import Tio, TioRequest
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _ref, _doc
from _tio import Tio, TioRequest

class Coding:
    """To test code and check docs"""

    def __init__(self, bot):
        self.bot = bot

    async def __before_invoke(self, ctx):
        await ctx.trigger_typing()

    @commands.cooldown(1, 8, BucketType.user)
    @commands.command(aliases=['se'])
    async def stack(self, ctx, siteName, *, text: str):
        """Queries given StackExchange website and gives you top results"""

        if siteName[0].islower() or not siteName in dir(se):
            await ctx.send(f"{siteName} does not appear to be in the StackExchange network."
                " Check the case and the spelling.")

        site = se.Site(getattr(se, siteName), self.bot.config['SE_KEY'])
        site.impose_throttling = True
        site.throttle_stop = False

        qs = site.search(intitle=text)[:3]
        if qs:
            emb = discord.Embed(title=text)
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

    # TODO: lua, java, javascript, asm
    documented = {
        'c': _doc.c_doc,
        'cpp': _doc.cpp_doc,
        'haskell': _doc.haskell_doc,
        'python': _doc.python_doc        
    }

    @commands.command(aliases=['doc'])
    async def documentation(self, ctx, lang, *, text: str):
        """Returns element reference from given language"""

        lang = lang.strip('`')

        if not lang.lower() in self.documented:
            return await ctx.send(f"{lang} not available. See {self.bot.config['PREFIX']}doclist for available ones.")

        await self.documented[lang.lower()](ctx, text.strip('`'))

    @commands.command()
    async def doclist(self, ctx):
        """Give available technos for reference command"""

        emb = discord.Embed(title="Available technologies for documentation command",
            description=f"`{'`, `'.join(self.documented)}`")

        await ctx.send(embed=emb)

    def get_content(_, tag):
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

    @commands.command()
    async def man(self, ctx, *, text: str):
        """Returns the manual's page for a linux command"""

        base_url = f'https://man.cx/{text}'
        url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

        async with aiohttp.ClientSession() as client_session:
            async with client_session.get(url) as response:
                if response.status != 200:
                    return await ctx.send('An error occurred (status code: {response.status}). Retry later.')

                soup = BeautifulSoup(await response.text(), 'lxml')

                nameTag = soup.find('h2', string='NAME\n')

                if not nameTag:
                    # No NAME, no page
                    return await ctx.send(f'No manual entry for `{text}`. (Debian)')

                # Get the two (or less) first parts from the nav aside
                # The first one is NAME, we already have it in nameTag
                contents = soup.find_all('nav', limit=2)[1].find_all('li', limit=3)[1:]

                if contents[-1].string == 'COMMENTS':
                    contents.remove(-1)

                title = self.get_content(nameTag)

                emb = discord.Embed(title=title, url=f'https://man.cx/{text}')
                emb.set_author(name='Debian Linux man pages')
                emb.set_thumbnail(url='https://www.debian.org/logos/openlogo-nd-100.png')

                for tag in contents:
                    h2 = tuple(soup.find(attrs={'name': tuple(tag.children)[0].get('href')[1:]}).parents)[0]
                    emb.add_field(name=tag.string, value=self.get_content(h2))

                await ctx.send(embed=emb)

    mapping = {
        'c': '#include <stdio.h>\nint main() {code}',
        'cpp': '#include <iostream>\nint main() {code}',
        'cs': 'using System;class Program {static void Main(string[] args) {code}}',
        'java': 'public class Main {public static void main(String[] args) {code}}',
        'rust': 'fn main() {code}',
        'd': 'import std.stdio; void main(){code}'
    }

    @commands.command(
help='''run <language> [--wrapped] [--stats] <code>

stats option displays more informations on execution consumption
wrapped allows you to not put main function in some languages : Java, C, C++ and C# currently''',
brief='Execute code in a given programming language'
        )
    async def run(self, ctx, language, *, code: str):
        """Execute code in a given programming language"""
        # Powered by tio.run

        options = {
            'stats': False,
            'wrapped': False
        }

        lang = language.strip('`').lower()
        code = code.split(' ')

        for i,option in enumerate(options):
            if f'--{option}' in code[:len(options) - i]:
                options[option] = True
                code.remove(f'--{option}')

        code = ' '.join(code)
        text = code.strip('`')

        if not text:
            # Ensures code isn't empty after removing options
            raise commands.MissingRequiredArgument(ctx.command.clean_params['code'])

        firstLine = text.splitlines()[0]
        if re.fullmatch(r'( |[0-9A-z]*)\b', firstLine):
            text = text[len(firstLine)+1:]

        if lang in self.bot.default:
            lang = self.bot.default[lang]
        if not lang in self.bot.languages:
            matches = '\n'.join([language for language in self.bot.languages if lang in language][:10])
            if lang == 'javascript':
                matches += "\nthe worst language ever"
            message = f"`{lang}` not available."
            if matches:
                message = message + f" Did you mean:\n{matches}"

            return await ctx.send(message)

        if options['wrapped']:
            

            if not (any(map(lambda x: lang.split('-')[0] == x, self.mapping))) or lang in ('cs-mono-shell', 'cs-csi'):
                return await ctx.send(f'`{lang}` cannot be wrapped')

            for beginning in self.mapping:
                if lang.split('-')[0] == beginning:
                    text = self.mapping[beginning].replace('code', text)
                    break

        site = Tio()
        req = TioRequest(lang, text)
        res = await site.send(req)
        
        output = res.result.decode('utf-8')
        # remove token
        cleaned = re.sub(re.escape(output[:16]), '', output)
        cleaned = re.sub('```', '\`\`\`', cleaned)

        if not options['stats']:
            try:
                start = cleaned.rindex("Real time: ")
                end = cleaned.rindex("%\nExit code: ")
                cleaned = cleaned[:start] + cleaned[end+2:]
            except ValueError:
                # Too much output removes this markers
                pass

        if len(cleaned) > 1991:
            # Mustn't exceed 2000 characters, counting ` and ph\n characters
            cleaned = cleaned[:1988] + '...'

        # ph, as placeholder, prevents Discord from taking the first line
        await ctx.send(f'```ph\n{cleaned}```')

    @commands.command()
    async def runlist(self, ctx):
        """Give available languages for run command"""

        emb = discord.Embed(title=f"{len(self.bot.languages)} available languages for run command")
        emb.add_field(name="Doesn't fit here",
            value='You can view them on [Github](https://github.com/FrenchMasterSword/RTFMbot/blob/master/languages.txt "and leave a star ! ^^")')

        await ctx.send(embed=emb)

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

    @commands.command(aliases=['ref'])
    async def reference(self, ctx, lang, *, text: str):
        """Returns element reference from given language"""

        lang = lang.strip('`')

        if not lang.lower() in self.referred:
            return await ctx.send(f"{lang} not available. See {self.bot.config['PREFIX']}reflist for available ones.")

        await self.referred[lang.lower()](ctx, text.strip('`'))

    @commands.command()
    async def reflist(self, ctx):
        """Give available technos for reference command"""

        emb = discord.Embed(title="Available technologies for reference command",
            description=f"`{'`, `'.join(self.referred)}`")

        await ctx.send(embed=emb)

def setup(bot):
    bot.add_cog(Coding(bot))
