from yaml import load as yaml_load

with open('config.yml', 'r') as file:
    config = yaml_load(file)

from bot import Codix

def run_bot():
    # loop = asyncio.get_event_loop()
    # log = logging.getLogger()

    bot = Codix(config)
    bot.run(bot.config['BOT_TOKEN'])


if __name__ == '__main__':
    run_bot()
