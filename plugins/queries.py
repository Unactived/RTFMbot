import aiohttp
import urllib.parse
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from datetime import datetime
from string import ascii_uppercase
from functools import reduce
import random
import re
import stackexchange as se
# from pytio import Tio, TioRequest
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from _tio import Tio, TioRequest


class Search:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['se'])
    async def stack(self, ctx, siteName, *, text: str):
        """Queries given StackExchange website and gives you top results"""

        if siteName[0].islower() or not siteName in dir(se):
            await ctx.send(f"{siteName} does not appear to be in the StackExchange network."
                " Check the case and the spelling.")

        site = se.Site(getattr(se, siteName), self.bot.config['SE_KEY'])
        site.impose_throttling = True
        site.throttle_stop = False

        async with ctx.typing():
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

    @commands.command()
    async def pythondoc(self, ctx, *, text: str):
        """Filters python.org results based on your query"""

        url = "https://docs.python.org/3/genindex-all.html"
        alphabet = '_' + ascii_uppercase

        async with ctx.typing():
            async with aiohttp.ClientSession() as client_session:
                async with client_session.get(url) as response:
                    if response.status != 200:
                        return await ctx.send('An error occurred (status code: {response.status}). Retry later.')

                    soup = BeautifulSoup(str(await response.text()), 'lxml')

                    def soup_match(tag):
                        return all(string in tag.text for string in text.strip().split()) and tag.name == 'li'

                    elements = soup.find_all(soup_match, limit=10)
                    links = [tag.select_one("li > a") for tag in elements]
                    links = [link for link in links if link is not None]

                    if not links:
                        return await ctx.send("No results")

                    content = [f"[{a.string}](https://docs.python.org/3/{a.get('href')})" for a in links]

                    emb = discord.Embed(title="Python 3 docs")
                    emb.add_field(name=f'Results for `{text}` :', value='\n'.join(content), inline=False)

                    await ctx.send(embed=emb)

    @commands.command(aliases=['cdoc', 'c++doc'])
    async def cppdoc(self, ctx, *, text: str):
        """Search something on cppreference"""

        base_url = 'https://cppreference.com/w/cpp/index.php?title=Special:Search&search=' + text
        url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

        async with ctx.typing():
            async with aiohttp.ClientSession() as client_session:
                async with client_session.get(url) as response:
                    if response.status != 200:
                        return await ctx.send('An error occurred (status code: {response.status}). Retry later.')

                    soup = BeautifulSoup(await response.text(), 'lxml')

                    uls = soup.find_all('ul', class_='mw-search-results')

                    if not len(uls):
                        return await ctx.send('No results')

                    if ctx.invoked_with == 'cdoc':
                        wanted = 'w/c/'
                        language = 'C'
                    else:
                        wanted = 'w/cpp/'
                        language = 'C++'

                    for elem in uls:
                        if wanted in elem.select_one("a").get('href'):
                            links = elem.find_all('a', limit=10)
                            break

                    content = [f"[{a.string}](https://en.cppreference.com/{a.get('href')})" for a in links]
                    emb = discord.Embed(title=f"{language} docs")
                    emb.add_field(name=f'Results for `{text}` :', value='\n'.join(content), inline=False)

                    await ctx.send(embed=emb)

    @commands.command(aliases=['man'])
    async def manpage(self, ctx, *, text: str):
        """Returns the manual's page for a linux command"""

        def get_content(tag):
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



        base_url = f'https://man.cx/{text}'
        url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

        async with ctx.typing():
            async with aiohttp.ClientSession() as client_session:
                async with client_session.get(url) as response:
                    if response.status != 200:
                        return await ctx.send('An error occurred (status code: {response.status}). Retry later.')

                    soup = BeautifulSoup(await response.text(), 'lxml')

                    nameTag = soup.find('h2', string='NAME\n')

                    if not nameTag:
                        # No NAME, no page
                        return await ctx.send(f'No manual entry for `{text}`. (Debian)')

                    # Get the three (or less) first parts from the nav aside
                    # The first one is NAME, we already have it in nameTag
                    contents = soup.find_all('nav', limit=2)[1].find_all('li', limit=3)[1:]

                    if contents[-1].string == 'COMMENTS':
                        contents.remove(-1)

                    title = get_content(nameTag)

                    emb = discord.Embed(title=title, url=f'https://man.cx/{text}')
                    emb.set_author(name='Debian Linux man pages',
                        icon_url='https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Openlogo-debianV2.'
                        'svg/640px-Openlogo-debianV2.svg.png?1538755715969')

                    for tag in contents:
                        h2 = tuple(soup.find(attrs={'name': tuple(tag.children)[0].get('href')[1:]}).parents)[0]
                        emb.add_field(name=tag.string, value=get_content(h2))

                    await ctx.send(embed=emb)

    @commands.command()
    async def run(self, ctx, lang, *, text: str):
        """Execute on a distant server and print results of a code in a given language"""
        
        language = lang.strip('`').lower()
        code = text.strip('`').strip('``')

        firstLine = code.splitlines()[0]
        if re.fullmatch(r'( |[0-9A-z]*)\b', firstLine):
            code = code[len(firstLine)+1:]

        site = Tio()
        req = TioRequest(language, code)
        res = site.send(req)
        
        if res.result == f"The language '{language}' could not be found on the server.\n":
            return await ctx.send(f"`{language}` isn't available. For a list of available"
                f"programming languages, do `{self.bot.config['PREFIX']}runlist`")

        output = res.result.decode('utf-8')
        cleaned = re.sub(re.escape(output[:16]), '', output)
        if len(cleaned) > 1994:
            cleaned = cleaned[1991:] + '...'

        # ph, as placeholder, prevents Discord from taking the first line
        await ctx.send(f'```ph\n{cleaned}```')

        # if res.result:
        #     colour = self.bot.config['GREEN']
        # elif res.error:
        #     colour = self.bot.config['RED']
        # else:
        #     await ctx.send('No output')

        # emb = discord.Embed(title=language, colour=colour)
        # emb.set_footer(text="Powered by tio.run")

        # # ph, as placeholder, prevents Discord from taking the first line
        # # for a markdown
        # if res.result:
        #     emb.add_field(name="Output", value=f"```ph\n{res.result}```")
        # if res.error:
        #     emb.add_field(name="Error", value=f"```ph\n{res.error}```")


        # await ctx.send(embed=emb)

    @commands.command()
    async def runlist(self, ctx):
        """Give available languages for run command"""

        # Exceeds 6000 characters for the Embed

        # languages = Tio().query_languages()
        # result = "'{}'".format("`, `".join(languages))

        # emb = discord.Embed(title="Available languages for run command",
        #     description=f'`{result}`')

        # await ctx.send(embed=emb)

        emb = discord.Embed(title="Available languages for run command")
        emb.add_field(name="Doesn't fit here", value="[See yourself](https://tio.run/#)")

        await ctx.send(embed=emb)

def setup(bot):
    bot.add_cog(Search(bot))
