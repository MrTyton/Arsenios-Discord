#!/usr/bin/env python
#-*- coding: utf-8 -*-

import importlib
from Bot import ChatBot
from pathlib import Path
from os.path import isfile
from itertools import groupby


class ArseniosBot(ChatBot):
    """
    Dumb Bot is a basic toy bot integration
    He has some built in functionality as well as webhook-bot
    integrations to provide a connection to webhooks

    WebHook data is stored in the 'shared' folder, so we
    allow Dumb Bot to access the shared pool
    """

    STATUS = "Beep Bloop Bork"

    def load_cog(self, extension):
        try:
            i = importlib.import_module(extension)
            i.setup(self)
        except Exception as e:
            self.logger(f'Could not load {extension}, broke with error "{e}"')
        return

    def load_extensions(self):
        if isfile(Path(self.DATA_FOLDER, f'{self.name}.extensions')):
            with open(Path(self.DATA_FOLDER, f'{self.name}.extensions'), 'r') as fp:
                for extension in fp.read().splitlines():
                    self.logger(f"Loading {extension}")
                    self.load_cog(extension)
        else:
            self.logger("There is no extension file, creating.")
            with open(Path(self.DATA_FOLDER, f'{self.name}.extensions'), 'w') as fp:
                fp.write("\n")
        return

    # Used to convert chars to emojis for /roll
    emojis = {f"{i}": x for i, x in enumerate([f":{x}:" for x in (
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine")])}

    def __init__(self, name):
        super(ArseniosBot, self).__init__(name)
        self.filegen = self._create_filegen("shared")

        self.load_extensions()

    @ChatBot.action('<Command>')
    async def help(self, args, mobj):
        """
        Return a link to a command reference sheet
        If you came here from !help help, you're out of luck
        """
        if args:
            key = f'{ChatBot.PREFIX}{args[0]}'
            if key in self.ACTIONS:
                t = self.pre_text(
                    f'Help for \'{key}\':{self.ACTIONS[key].__doc__}')
                return await self.message(mobj.channel, t)
        output = 'Thank you for choosing Arsenios™ for your channel\nIf you have any bug reports, please tell @MrTyton#5093\nIf you want to peek under the hood, go to https://github.com/MrTyton/Arsenios-Discord\n\n'
        output += 'Here are the available commands\n'
        output += '<> means that the input is optional, [] means that the input is required\n\n'
        for k, g in groupby(self.ACTIONS.keys(),
                            key=lambda x: self.ACTIONS[x].__module__):
            output += f'{k}:\n'.replace("extensions.", "").replace("__", "")
            for cur in g:
                c = f'{cur}'
                output += f'\t* {c} {self.HELPMSGS.get(c, "")}\n'
        output += f'\nFor more info on each command, use \'{ChatBot.PREFIX}help command\''
        return await self.message(mobj.channel, self.pre_text(output))


if __name__ == "__main__":
    d = ArseniosBot("Arsenios")
    d.run()
    pass

# end
