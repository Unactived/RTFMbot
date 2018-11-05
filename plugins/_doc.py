# import sys
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import os
import urllib.parse
from functools import partial
from string import ascii_uppercase

import aiohttp
import discord
from bs4 import BeautifulSoup


async def pythondoc(ctx, text: str):
    """Filters python.org results based on your query"""

    url = "https://docs.python.org/3/genindex-all.html"
    alphabet = '_' + ascii_uppercase

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

            path = os.path.join("./RTFMbot-master/assets", "python.png")
            file = discord.File(path, "python_logo.png")

            emb = discord.Embed(title="Python 3 docs")
            emb.set_thumbnail(url='attachment://python_logo.png')
            emb.add_field(name=f'Results for `{text}` :', value='\n'.join(content), inline=False)

            await ctx.send(embed=emb)

async def _cppreference(language, ctx, text: str):
    """Search something on cppreference"""

    base_url = 'https://cppreference.com/w/cpp/index.php?title=Special:Search&search=' + text
    url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

    async with aiohttp.ClientSession() as client_session:
        async with client_session.get(url) as response:
            if response.status != 200:
                return await ctx.send(f'An error occurred (status code: {response.status}). Retry later.')

            soup = BeautifulSoup(await response.text(), 'lxml')

            uls = soup.find_all('ul', class_='mw-search-results')

            if not len(uls):
                return await ctx.send('No results')

            if language == 'C': 
                wanted = 'w/c/'
                url = 'https://wikiprogramming.org/wp-content/uploads/2015/05/c-logo-150x150.png'
            else:
                wanted = 'w/cpp/'
                url = 'https://isocpp.org/files/img/cpp_logo.png'

            for elem in uls:
                if wanted in elem.select_one("a").get('href'):
                    links = elem.find_all('a', limit=10)
                    break

            content = [f"[{a.string}](https://en.cppreference.com/{a.get('href')})" for a in links]
            emb = discord.Embed(title=f"{language} docs")
            emb.set_thumbnail(url=url)
            emb.add_field(name=f'Results for `{text}` :', value='\n'.join(content), inline=False)

            await ctx.send(embed=emb)

cdoc = partial(_cppreference, 'C')
cppdoc = partial(_cppreference, 'C++')