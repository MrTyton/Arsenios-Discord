from Bot import ChatBot, Bot
from random import choice
from os.path import isfile, join
from os.path import isfile, join
from pathlib import Path
from os import listdir


class REACTIONBOT():
    
    def __init__(self, bot):
        self.bot = bot
        self.bot.get_images = self.get_images
        self.create_reactions(self.bot)

    @staticmethod
    def get_images(self, name):
        files = [f for f in listdir(Path(f'{self.PICTURE_FOLDER}', name)) if isfile(join(Path(f'{self.PICTURE_FOLDER}', name), f))]
        
        return join(Path(f'{self.PICTURE_FOLDER}', name), choice(files)) 
    
    @staticmethod
    def create_reactions(self):
        """
        This will scan the picture folder for any folders and, if possible, create a reaction command for it.
        If you want to add or remove reaction commands, simply add or remove a folder and it will register it on the next reboot of the bot.
        """
        folders = sorted([f for f in listdir(Path(f'{self.PICTURE_FOLDER}')) if not isfile(join(Path(f'{self.PICTURE_FOLDER}'), f))])
        for cur in folders:
            registering = lambda selfie, args, mobj: selfie.client.send_file(mobj.channel, selfie.get_images(self, f'{mobj.content[1:]}'))
            registering.__doc__ = f"""
        Posts a {cur} reaction.
        """
            if cur not in self.ACTIONS:
                fname = f'{self.PREFIX}{cur}'
                self.ACTIONS[fname] = registering
                self.HELPMSGS[fname] = ""
                self.logger(f"Registered {cur}")
            else:
                self.logger(f"Cannot register {cur}, another function with the same name exists.")
        return
        
        
def setup(bot):
    REACTIONBOT(bot)