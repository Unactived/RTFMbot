import aiohttp
import urllib.parse
import html
import re
from bs4 import BeautifulSoup
from bs4.element import NavigableString
import discord

def html_to_md(string):
    string = re.sub('<code>|</code>', '`', string)
    string = re.sub('<strong>|</strong>', '**', string)
    string = re.sub('<em>|</em>', '*', string)

    return html.unescape(string)

async def htmlref(ctx, text):

    text = text.strip('`').strip('<').strip('>')

    base_url = f"https://developer.mozilla.org/en-US/docs/Web/HTML/Element/{text}"
    url = urllib.parse.quote_plus(base_url, safe=';/?:@&=$,><-[]')

    async with ctx.typing():
            async with aiohttp.ClientSession() as client_session:
                async with client_session.get(url) as response:
                    if response.status != 200:
                        return await ctx.send(f'An error occurred (status code: {response.status}). Retry later.')

                    body = BeautifulSoup(await response.text(), 'lxml').find('body')

                    if body.get('class')[0] == 'error':
                    	# 404
                    	return await ctx.send(f'`{text}` does not appear to be avalid HTML tag.')

                    # Two empty p tags before it
                    contents = body.find(id='wikiArticle').find_all('p', limit=3)[2].contents

                    result = []

                    for tag in contents:
                        if tag.name == 'a':
                            result.append(f"[{tag.text}](https://developer.mozilla.org{tag.get('href')})")
                        elif type(tag) == NavigableString:
                            result.append(str(tag.string))
                        else:
                            result.append(html_to_md(str(tag)))

                    emb = discord.Embed(title=text, description=''.join(result))

                    emb.set_author(name='HTML5 Reference',
                        icon_url="https://www.w3.org/html/logo/badge/html5-badge-h-solo.png",)

                    await ctx.send(embed=emb)









