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

                result = []

                for tag in contents:
                    if tag.name == 'a':
                        result.append(f'''[{tag.text}](https://developer.mozilla.org{tag.get('href')} "{tag.get('title')}")''')
                    elif type(tag) == NavigableString:
                        result.append(str(tag.string))
                    else:
                        result.append(_used.html_to_md(str(tag)))

                return ''.join(result)

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
