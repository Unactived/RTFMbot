import functools

import aiohttp
from discord.ext import commands

def get_raw(link):
    """Returns the url for raw version on a hastebin-like"""

    link = link.strip('<>/') # Allow for no-embed links

    authorized = (
        'https://hastebin.com',
        'https://gist.github.com',
        'https://gist.githubusercontent.com'
    )

    if not any([link.startswith(url) for url in authorized]):
        raise commands.BadArgument(message=f"I only accept links from {', '.join(authorized)}. (Starting with 'http').")

    domain = link.split('/')[2]

    if domain == 'hastebin.com':
        if '/raw/' in link:
            return link
        token = link.split('/')[-1]
        if '.' in token:
            token = token[:token.rfind('.')] # removes extension
        return f'https://hastebin.com/raw/{token}'
    else:
        # Github uses redirection so raw -> usercontent and no raw -> normal
        # We still need to ensure we get a raw version after this potential redirection
        if '/raw' in link:
            return link
        return link + '/raw'

def typing(func):
    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        context = args[0] if isinstance(args[0], commands.Context) else args[1]
        async with context.typing():
            await func(*args, **kwargs)
    return wrapped
