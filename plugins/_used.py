import functools
import html
import re

import aiohttp
import bs4
from discord.ext import commands

def html_to_md(string):
    string = re.sub('<code>|</code>', '`', string)
    string = re.sub('<strong>|</strong>|<b>|</b>', '**', string)
    string = re.sub('<em>|</em>|<i>|</i>', '*', string)
    string = re.sub('<span class="[a-zA-Z0-9]*">|</span>', '', string)

    return html.unescape(string)

def tags_to_text(contents, url):
    result = []
    domain = url[:url.index('/', 8)]
    for tag in contents:
        if type(tag) == bs4.element.Tag and tag.name == 'a':
            if not domain in tag.get('href'):
                href = f"{domain}{tag.get('href')}"
            else:
                href = tag.get('href')
            link = f"[{tag.string}]({href})"
            if tag.get('title') is not None:
                link = f'''{link[:-1]} "{tag.get('title')}")'''
            result.append(link)
        elif type(tag) == bs4.element.NavigableString:
            result.append(str(tag.string))
        else:
            result.append(html_to_md(str(tag)))

    return ''.join(result)

def typing(func):
    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        context = args[0] if isinstance(args[0], commands.Context) else args[1]
        async with context.typing():
            await func(*args, **kwargs)
    return wrapped
