from pathlib import Path
from os.path import isfile


class ERRORBOT:

    def __init__(self, bot):
        self.bot = bot
        self.bot.error = self.error

    async def error(self, channel, message):
        if isfile(Path(
                self.bot.DATA_FOLDER,
                f'{self.bot.name}.error.png')):
            await self.bot.client.send_file(channel, Path(
                self.bot.DATA_FOLDER,
                f'{self.bot.name}.error.png'))
        return await self.bot.message(channel, message)


def setup(bot):
    ERRORBOT(bot)
