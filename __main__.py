#!/usr/bin/env python3

from yaml import safe_load as yaml_load
from os.path import isfile
from sys import exit as sys_exit
from shutil import copyfile
import asyncio
import aiohttp
import traceback

from bot import RTFM
from db import Database

CONFIG_FILE = 'config.yml'
CONFIG_TEMPLATE = 'config_example.yml'

if not isfile(CONFIG_FILE):
    if not isfile(CONFIG_TEMPLATE):
        print('Configuration file "%s" missing, exiting.' % CONFIG_FILE)
        sys_exit(1)

    copyfile(CONFIG_TEMPLATE, CONFIG_FILE)
    print('Configuration file "%s" generated using template.' % CONFIG_FILE)
    print('Please edit that file in order to run the bot.')
    sys_exit(1)

with open(CONFIG_FILE) as file:
    config = yaml_load(file)
    if not config.get('BOT_TOKEN'):
        print('Discord token is missing in the configuration file, exiting.')
        sys_exit(1)

async def run_bot():

    try:
        db = await Database.create(config['POSTGRESQL'])
    except:
        traceback.print_exc()
        print('Could not set up PostgreSQL, exiting.')
        sys_exit(1)

    bot = RTFM(config, db)

    async with aiohttp.ClientSession() as session:
        async with bot:
            bot.session = session

            await bot.start(bot.config['BOT_TOKEN'])


if __name__ == '__main__':
    asyncio.run(run_bot())
