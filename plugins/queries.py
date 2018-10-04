import aiohttp
import urllib.parse
import discord
from discord.ext import commands
from bs4 import BeautifulSoup
from datetime import datetime
from string import ascii_uppercase
import random
import re

import stackexchange as se

class Search:
    def __init__(self, bot):
        pass

    @commands.command(aliases=['se'])
    async def stack(self, ctx, *, text: str):
        """Queries StackOverflow and gives you top results"""

        siteName = text.split()[0]

        if not siteName in dir(se):
            await ctx.send(f"{siteName} does not appear to be in the StackExchange network."
                " Check the case and the spelling.")

        site = se.Site(getattr(se, siteName))
        site.impose_throttling = True
        site.throttle_stop = False

        async with ctx.typing():
            terms = text[text.find(' ')+1:]
            qs = site.search(intitle=terms)[:3]
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

    # @commands.command(aliases=['ddg'])
    # async def duckduckgo(self, ctx, *, text: str):
    #     """Search something on DuckDuckGo engine"""

    #     base_url = "https://duckduckgo.com/?q="
    #     base_url += text + "&t=ffab&ia=web"

    #     url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

    #     async with ctx.typing():
    #         async with aiohttp.ClientSession() as client_session:
    #             async with client_session.get(url) as response:
    #                 if response.status != 200:
    #                     return await ctx.send('An error occurred (status code: {response.status}). Retry later.')

    #                 soup = BeautifulSoup(await response.text(), 'lxml')

    # @commands.command()
    # async def gitdoc(self, ctx, *, text: str):
    #     """"""

    @commands.command(aliases=['man'])
    async def manpage(self, ctx, *, text: str):
        """Returns the manual's page for a linux command"""

        base_url = f'https://man.cx/{text}'
        url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

        async with ctx.typing():
            async with aiohttp.ClientSession() as client_session:
                async with client_session.get(url) as response:
                    if response.status != 200:
                        return await ctx.send('An error occurred (status code: {response.status}). Retry later.')

                    soup = BeautifulSoup(await response.text(), 'lxml')

                    if 'Search results' in soup.find('h2').text:
                        # We didn't find a man page.
                        return await ctx.send(f'No manual entry for `{text}`. (Debian)')

                    # That's some bad HTML scraping
                    title = soup.find('h2', text='NAME\n').next_sibling.next_sibling.string.replace('\n', ' ')

                    # Really bad
                    synopsis = soup.find('table').contents[1].contents[3].contents[1].text

                    # I feel dead inside
                    author = soup.find('h2', text=re.compile('AUTHOR')).next_sibling.next_sibling.string.replace('\n', ' ')

                    emb = discord.Embed(title=title, url=f'https://man.cx/{text}', author='Linux man pages')
                    emb.add_field(name="SYNOPSIS", value=synopsis, inline=False)
                    emb.add_field(name="AUTHOR", value=author, inline=False)

                    await ctx.send(embed=emb)

def setup(bot):
    bot.add_cog(Search(bot))
