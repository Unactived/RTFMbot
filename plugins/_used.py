import html
import re

import aiohttp

def html_to_md(string):
    string = re.sub('<code>|</code>', '`', string)
    string = re.sub('<strong>|</strong>', '**', string)
    string = re.sub('<em>|</em>', '*', string)
    string = re.sub('<span class="seoSummary">|</span>', '', string)

    return html.unescape(string)
