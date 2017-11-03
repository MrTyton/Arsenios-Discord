from random import choice
from os.path import isfile, join
from pathlib import Path
from os import listdir


class REACTIONBOT():

    def __init__(self, bot):
        self.bot = bot
        self.bot.get_images = self.get_images
        self.create_reactions()

    def get_images(self, name):
        files = [
            f for f in listdir(
                Path(
                    f'{self.bot.PICTURE_FOLDER}',
                    name)) if isfile(
                join(
                    Path(
                        f'{self.bot.PICTURE_FOLDER}',
                        name),
                    f))]

        return join(Path(f'{self.bot.PICTURE_FOLDER}', name), choice(files))

    def create_reactions(self):
        """
        This will scan the picture folder for any folders and, if possible, create a reaction command for it.
        If you want to add or remove reaction commands, simply add or remove a folder and it will register it on the next reboot of the bot.
        """

        folders = sorted([f for f in listdir(Path(f'{self.bot.PICTURE_FOLDER}')) if not isfile(
            join(Path(f'{self.bot.PICTURE_FOLDER}'), f))])
        for cur in folders:
            def registering(selfie, args, mobj): return selfie.client.send_file(
                mobj.channel, selfie.get_images(f'{mobj.content.split(" ")[0][1:]}'))
            registering.__doc__ = f"""
        Posts a {cur} reaction.
        """
            if cur not in self.bot.ACTIONS:
                fname = f'{self.bot.PREFIX}{cur}'
                self.bot.ACTIONS[fname] = registering
                self.bot.HELPMSGS[fname] = ""
                self.bot.logger(f"Registered {cur}")
            else:
                self.bot.logger(
                    f"Cannot register {cur}, another function with the same name exists.")
        return


def setup(bot):
    REACTIONBOT(bot)
