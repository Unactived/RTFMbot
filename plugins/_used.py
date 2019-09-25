import functools
import re
from urllib.parse import urlparse

import aiohttp
from discord.ext import commands


pastebins = {}
def pastebin(path_re):
    def register(func):
        pastebins[func.__name__.replace('_', '.')] = (func, re.compile(path_re))
        return func
    return register


def get_raw(link):
    """Returns the url for raw version on a hastebin-like"""
    address = urlparse(link.strip('<>/'))  # Allow for no-embed links
    if address.scheme not in ('https', 'http'):
        raise commands.BadArgument(message=f"Please specify the http scheme to use.")
    func, regexp = pastebins.get(address.netloc, (None, None))
    if not func:
        raise commands.BadArgument(message=f"I only accept links from {', '.join(pastebins)}.")
    match = regexp.match(address.path)
    if not match:
        raise commands.BadArgument(message=f"Wrong URI for {address.netloc}.")

    return func(address, match)


@pastebin(r'/(raw/(\w+)|(\w+)(\..*)?)')
def hastebin_com(_address, match):
    return 'https://hastebin.com/raw/' + (match.group(2) or match.group(3))


@pastebin(r'/[^/]+/[0-9a-fA-F]{32}/raw/[0-9a-fA-F]{40}/.*')
def gist_githubusercontent_com(address, _match):
    return address.geturl()


@pastebin(r'/[^/]+/[0-9a-fA-F]{32}(/raw)?(/)?')
def gist_github_com(address, match):
    return 'https://gist.github.com{}{}{}'.format(
        address.path,
        '' if match.group(2) else '/',
        '' if match.group(1) else 'raw')


@pastebin(r'/(\w{10})(\..*)?')
def bin_drlazor_be(address, _match):
    return address.geturl()


async def paste(text):
    """Return an online bin of given text"""

    async with aiohttp.ClientSession() as aioclient:
        post = await aioclient.post('https://hastebin.com/documents', data=text)
        if post.status == 200:
            response = await post.text()
            return f'https://hastebin.com/{response[8:-2]}'

        # Rollback bin
        post = await aioclient.post("https://bin.drlazor.be", data={'val':text})
        if post.status == 200:
            return post.url


def typing(func):
    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        context = args[0] if isinstance(args[0], commands.Context) else args[1]
        async with context.typing():
            await func(*args, **kwargs)
    return wrapped
