import re
import urllib.parse
from functools import partial
# import sys

import aiohttp
import discord
from bs4 import BeautifulSoup
from bs4.element import NavigableString

# sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import _used

async def _process_mozilla_doc(ctx, url):

    async with aiohttp.ClientSession() as client_session:
        async with client_session.get(url) as response:
            if response.status == 404:
                return await ctx.send(f'No results')
            if response.status != 200:
                return await ctx.send(f'An error occurred (status code: {response.status}). Retry later.')

            body = BeautifulSoup(await response.text(), 'lxml').find('body')

    # if body.get('class')[0] == 'error':
    #     # 404
    #     return await ctx.send(f'No results for `{text}`')

    # First tag not empty
    contents = body.find(id='wikiArticle').find(lambda x: x.name == 'p' and x.text).contents

    return _used.tags_to_text(contents, url)

async def html_ref(ctx, text):

    text = text.strip('<').strip('>')

    base_url = f"https://developer.mozilla.org/en-US/docs/Web/HTML/Element/{text}"
    url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

    output = await _process_mozilla_doc(ctx, url)
    if type(output) != str:
        # Error message already sent
        return

    emb = discord.Embed(title=text, description=output, url=url)
    emb.set_author(name='HTML5 Reference')
    emb.set_thumbnail(url="https://www.w3.org/html/logo/badge/html5-badge-h-solo.png")

    await ctx.send(embed=emb)

async def _http_ref(part, ctx, text):

    base_url = f"https://developer.mozilla.org/en-US/docs/Web/HTTP/{part}/{text}"
    url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

    output = await _process_mozilla_doc(ctx, url)
    if type(output) != str:
        # Error message already sent
        return

    emb = discord.Embed(title=text, description=output, url=url)
    emb.set_author(name='HTTP protocol')
    emb.set_thumbnail(url='https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/HTTP_logo.svg/1280px-HTTP_logo.svg.png')

    await ctx.send(embed=emb)

http_headers = partial(_http_ref, 'Headers')
http_methods = partial(_http_ref, 'Methods')
http_status = partial(_http_ref, 'Status')
csp_directives = partial(_http_ref, 'Headers/Content-Security-Policy')

async def _git_main_ref(part, ctx, text):

    if part and text == 'git':
        # just 'git'
        part = ''
    if not part and not text.startswith('git'):
        # gittutorial, giteveryday...
        part = 'git'
    base_url = f"https://git-scm.com/docs/{part}{text}"
    url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

    async with aiohttp.ClientSession() as client_session:
        async with client_session.get(url) as response:
            if response.status != 200:
                return await ctx.send(f'An error occurred (status code: {response.status}). Retry later.')
            if str(response.url) == 'https://git-scm.com/docs':
                # Website redirects to home page
                return await ctx.send(f'No results')

            soup = BeautifulSoup(await response.text(), 'lxml')
            sectors = soup.find_all('div', {'class': 'sect1'}, limit=3)
    
            title = sectors[0].find('p').text

            emb = discord.Embed(title=title, url=url)
            emb.set_author(name='Git reference')
            emb.set_thumbnail(url='https://git-scm.com/images/logo@2x.png')

            for tag in sectors[1:]:
                content = '\n'.join([_used.tags_to_text(p.contents, url) for p in tag.find_all(lambda x: x.name in ['p', 'pre'])])
                emb.add_field(name=tag.find('h2').text, value=content[:1024])

            await ctx.send(embed=emb)

async def sql_ref(ctx, text):
    text = text.strip('`').lower()
    if text in ('check', 'unique', 'not null'): text += ' constraint'
    text = re.sub(' ', '-', text)

    base_url = f"http://www.sqltutorial.org/sql-{text}/"
    url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

    async with aiohttp.ClientSession() as client_session:
        async with client_session.get(url) as response:
            if response.status != 200:
                return await ctx.send(f'An error occurred (status code: {response.status}). Retry later.')

            body = BeautifulSoup(await response.text(), 'lxml').find('body')
            intro = body.find(lambda x: x.name == 'h2' and 'Introduction to ' in x.string)
            title = body.find('h1').string

            ps = []
            for tag in tuple(intro.next_siblings):
                if tag.name == 'h2' and tag.text.startswith('SQL '): break
                if tag.name == 'p':
                    ps.append(tag)

            description = '\n'.join([_used.tags_to_text(p.contents, url) for p in ps])[:2048]

            emb = discord.Embed(title=title, url=url, description=description)
            emb.set_author(name='SQL Reference')
            emb.set_thumbnail(url='https://users.soe.ucsc.edu/~kunqian/logos/sql-logo.png')

            await ctx.send(embed=emb)

git_ref = partial(_git_main_ref, 'git-')
git_tutorial_ref = partial(_git_main_ref, '')
