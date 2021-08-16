import functools

import aiohttp
import discord
import re
from discord.ext import commands
from yaml import safe_load as yaml_load

from _tio import Tio

wrapping = {
    'c': '#include <stdio.h>\nint main() {code}',
    'cpp': '#include <iostream>\nint main() {code}',
    'cs': 'using System;class Program {static void Main(string[] args) {code}}',
    'java': 'public class Main {public static void main(String[] args) {code}}',
    'rust': 'fn main() {code}',
    'd': 'import std.stdio; void main(){code}',
    'kotlin': 'fun main(args: Array<String>) {code}'
}

with open('default_langs.yml', 'r') as file:
    default_langs = yaml_load(file)

def prepare_payload(payload):
    no_code = False

    try:
        language,text = re.split(r'\s+', payload, maxsplit=1)
    except ValueError:
        # single word : no code yet no file attached
        emb = discord.Embed(title='SyntaxError',description=f"Command `run` missing a required argument: `code`",colour=0xff0000)
        return ('', emb, True)

    return (language, text, False)

class RerunBtn(discord.ui.Button):
    def __init__(self, bot, **kwargs):
        super().__init__(**kwargs)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        message = await interaction.message.channel.fetch_message(interaction.message.reference.message_id)

        prefixes = [f'<@!{self.bot.user.id}> ', f'<@{self.bot.user.id}> ']
        prefixes.append(self.bot.prefixes.get(interaction.guild_id) or self.bot.config['PREFIX'])

        payload = message.content

        # we need to strip the prefix and command name ('do run '), the prefix 
        # having multiple and even custom possible values
        for prefix in prefixes:
            if payload.startswith(prefix):
                payload = payload[len(prefix)+4:]
                break

        language,text,errored = prepare_payload(payload)

        if errored:
            return await interaction.message.edit(embed=text)

        result = await execute_run(self.bot, language, text)

        await interaction.message.edit(content=result)
        # self.stop()

class Refresh(discord.ui.View):
    def __init__(self, bot, no_rerun, timeout=300):
        super().__init__()

        item = RerunBtn(bot=bot, label='Run again', style=discord.ButtonStyle.grey, emoji='🔄', disabled=no_rerun)

        self.add_item(item)

        self.children.reverse() # Run again first

    @discord.ui.button(label='Delete', style=discord.ButtonStyle.grey, emoji='🗑')
    async def delete(self, button: discord.ui.Button, interaction: discord.Interaction):
        await interaction.message.delete()
        self.stop()


async def execute_run(bot, language, code, rerun=False) -> tuple:
    # Powered by tio.run

    options = {
    '--stats': False,
    '--wrapped': False
    }

    lang = language.strip('`').lower()

    optionsAmount = len(options)

    # Setting options and removing them from the beginning of the command
    # options may be separated by any single whitespace, which we keep in the list
    code = re.split(r'(\s)', code, maxsplit=optionsAmount)

    for option in options:
        if option in code[:optionsAmount*2]:
            options[option] = True
            i = code.index(option)
            code.pop(i)
            code.pop(i) # remove following whitespace character

    code = ''.join(code)

    compilerFlags = []
    commandLineOptions = []
    args = []
    inputs = []

    lines = code.split('\n')
    code = []
    for line in lines:
        if line.startswith('input '):
            inputs.append(' '.join(line.split(' ')[1:]).strip('`'))
        elif line.startswith('compiler-flags '):
            compilerFlags.extend(line[15:].strip('`').split(' '))
        elif line.startswith('command-line-options '):
            commandLineOptions.extend(line[21:].strip('`').split(' '))
        elif line.startswith('arguments '):
            args.extend(line[10:].strip('`').split(' '))
        else:
            code.append(line)

    inputs = '\n'.join(inputs)

    code = '\n'.join(code)

    # common identifiers, also used in highlight.js and thus discord codeblocks
    quickmap = {
        'asm': 'assembly',
        'c#': 'cs',
        'c++': 'cpp',
        'csharp': 'cs',
        'f#': 'fs',
        'fsharp': 'fs',
        'js': 'javascript',
        'nimrod': 'nim',
        'py': 'python',
        'q#': 'qs',
        'rs': 'rust',
        'sh': 'bash',
    }

    if lang in quickmap:
        lang = quickmap[lang]

    if lang in default_langs:
        lang = default_langs[lang]
    if not lang in bot.languages:
        matches = []
        i = 0
        for language in bot.languages:
            if language.startswith(lang[:3]):
                matches.append(language)
                i += 1
                if i == 10:
                    break
        matches = '\n'.join(matches)

        output = f"`{lang}` not available."
        if matches:
            output = output + f" Did you mean:\n{matches}"

        return output

    code = code.strip('`')

    if '\n' in code:
        firstLine = code.splitlines()[0]
        if re.fullmatch(r'([0-9A-z]*)\b', firstLine):
            code = code[len(firstLine)+1:]


    if options['--wrapped']:
        if not (any(map(lambda x: lang.split('-')[0] == x, wrapping))) or lang in ('cs-mono-shell', 'cs-csi'):
            return f'`{lang}` cannot be wrapped.'

        for beginning in wrapping:
            if lang.split('-')[0] == beginning:
                code = wrapping[beginning].replace('code', code)
                break

    tio = Tio(lang, code, compilerFlags=compilerFlags, inputs=inputs, commandLineOptions=commandLineOptions, args=args)

    result = await tio.send()

    if not options['--stats']:
        try:
            start = result.rindex("Real time: ")
            end = result.rindex("%\nExit code: ")
            result = result[:start] + result[end+2:]
        except ValueError:
            # Too much output removes this markers
            pass

    if len(result) > 1992 or result.count('\n') > 40:
        # If it exceeds 2000 characters (Discord longest message), counting ` and ph\n characters
        # Or if it floods with more than 40 lines
        # Create a hastebin and send it back
        link = await paste(result)

        if link is None:
            output = "Your output was too long, but I couldn't make an online bin out of it."
        else:
            output = f'Output was too long (more than 2000 characters or 40 lines) so I put it here: {link}'

        return output

    zero = '\N{zero width space}'
    output = re.sub('```', f'{zero}`{zero}`{zero}`{zero}', result)

    # p, as placeholder, prevents Discord from taking the first line
    # as a language identifier for markdown and remove it

    return f'```p\n{output}```'


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

async def paste(text):
    """Return an online bin of given text"""

    async with aiohttp.ClientSession() as aioclient:
        post = await aioclient.post('https://hastebin.com/documents', data=text)
        if post.status == 200:
            response = await post.text()
            return f'https://hastebin.com/{response[8:-2]}'

        # Rollback bin
        post = await aioclient.post("https://bin.readthedocs.fr/new", data={'code':text, 'lang':'txt'})
        if post.status == 200:
            return post.url


def typing(func):
    @functools.wraps(func)
    async def wrapped(*args, **kwargs):
        context = args[0] if isinstance(args[0], commands.Context) else args[1]
        async with context.typing():
            await func(*args, **kwargs)
    return wrapped
