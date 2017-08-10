#!/usr/bin/env python
#-*- coding: utf-8 -*-


from Bot import ChatBot, Bot
from discord import Embed, Color
from pathlib import Path
from os import listdir
from os.path import isfile, join
import pickle
from asyncio import Lock, sleep
from collections import defaultdict
from datetime import datetime

import importlib

class ArseniosBot(ChatBot):
    """
    Dumb Bot is a basic toy bot integration
    He has some built in functionality as well as webhook-bot
    integrations to provide a connection to webhooks

    WebHook data is stored in the 'shared' folder, so we
    allow Dumb Bot to access the shared pool
    """

    STATUS = "Beep Bloop Bork"
        
    def load_quotes(self):
        """
        Loads quotes from quotes pickle file
        """
        if isfile(Path(self.DATA_FOLDER, f'{self.name}.data')):
            with open(Path(self.DATA_FOLDER, f'{self.name}.data'), 'rb')  as fp:
                quotes = pickle.load(fp)
                if not quotes:
                    quotes = {}
        else:
            self.logger("There is no quotes file, creating.")
            with open(Path(self.DATA_FOLDER, f'{self.name}.data'), 'wb')  as fp:
                quotes = {}
                pickle.dump(quotes, fp)
        return quotes
            
    def load_notifications(self):
        """
        Loads notification settings from pickle file
        """
        if isfile(Path(self.DATA_FOLDER, f'{self.name}.notifications')):
            with open(Path(self.DATA_FOLDER, f'{self.name}.notifications'), 'rb') as fp:
                notifications = pickle.load(fp)
                if not notifications:
                    notifications = defaultdict(set)
        else:
            self.logger("There is no notification file, creating.")
            with open(Path(self.DATA_FOLDER, f'{self.name}.notifications'), 'wb') as fp:
                notifications = defaultdict(set)
                pickle.dump(notifications, fp)
                
        return notifications
            
    def save_notifications(self):
        """
        Save notification settings to pickle file.
        """
        with open(Path(self.DATA_FOLDER, f'{self.name}.notifications'), 'wb')  as fp:
            pickle.dump(self.notifications, fp)
        return
    
    
    def save_quotes(self):
        """
        Save quotes to quote pickle file.
        """
        with open(Path(self.DATA_FOLDER, f'{self.name}.data'), 'wb')  as fp:
            pickle.dump(self.quotes, fp)
        return
    
    def load_cog(self, extension): 
        i = importlib.import_module(extension)
        i.setup(self)
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
    emojis = {f"{i}":x for i, x in enumerate([f":{x}:" for x in
        ("zero", "one", "two", "three", "four", 
         "five", "six", "seven", "eight", "nine")])}

    def __init__(self, name):
        super(ArseniosBot, self).__init__(name)
        self.filegen = self._create_filegen("shared")
        self.quotes = self.load_quotes()
        self.quote_lock = Lock()
        self.notifications = self.load_notifications()
        self.notification_lock = Lock()
        self.sleepers = set()
        self.sleepers_lock = Lock()
        self.create_reactions()
        self.emojis = {}
        
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
                t = self.pre_text(f'Help for \'{key}\':{self.ACTIONS[key].__doc__}')
                return await self.message(mobj.channel, t)
        output = 'Thank you for choosing Arsenios™ for your channel\nIf you have any bug reports, please tell @MrTyton#5093\n\n'
        output += 'Here are the available commands\n'
        output += '<> means that the input is optional, [] means that the input is required\n\n'
        for c in [f'{k}' for k in self.ACTIONS.keys()]:
            output += f'* {c} {self.HELPMSGS.get(c, "")}\n'
        output += f'\nFor more info on each command, use \'{ChatBot.PREFIX}help command\''
        return await self.message(mobj.channel, self.pre_text(output))

    
        

    

    def get_images(self, name):
        files = [f for f in listdir(Path(f'{self.PICTURE_FOLDER}', name)) if isfile(join(Path(f'{self.PICTURE_FOLDER}', name), f))]
        
        return join(Path(f'{self.PICTURE_FOLDER}', name), choice(files)) 
    
    def create_reactions(self):
        """
        This will scan the picture folder for any folders and, if possible, create a reaction command for it.
        If you want to add or remove reaction commands, simply add or remove a folder and it will register it on the next reboot of the bot.
        """
        folders = sorted([f for f in listdir(Path(f'{self.PICTURE_FOLDER}')) if not isfile(join(Path(f'{self.PICTURE_FOLDER}'), f))])
        for cur in folders:
            registering = lambda selfie, args, mobj: selfie.client.send_file(mobj.channel, selfie.get_images(f'{mobj.content[1:]}'))
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
    
    @ChatBot.action('<String>|<add>[String]')
    async def quote(self, args, mobj):
        """
        Quote references.
        
        Using !quote will give a random quote.
        Using !quote add <Key> <Text> will add the text as a quote under the key <Key>
        Using !quote remove <Key> will remove the quote from the database
        Using !quote <Key> will print out the quote
        """
        if len(args) == 0:
            if len(self.quotes) == 0:
                return await self.message(mobj.channel, "No quotes in the database")
            option = choice(list(self.quotes.keys()))
            embd = Embed(
            title=option,
            colour=Color(0x7289da)
            )
            
            value = self.quotes[option]
            embd.add_field(name=f"{value[0]}", value=f"{value[1]}")
            return await self.embed(mobj.channel, embd)
        elif args[0].lower() == "add" and len(args) > 2:
            key = args[1].lower()
            if key in self.quotes:
                return await self.message(mobj.channel, "Key is already in quotes database.")
            value = [mobj.author, " ".join(args[2:]).strip()]
            self.quotes[key] = value
            await self.quote_lock.acquire()
            self.save_quotes()
            self.quote_lock.release()
            return await self.message(mobj.channel, f"Added quote {key}.")
        elif args[0].lower() == "remove" and len(args) == 2:
            key = args[1].lower()
            if key in self.quotes:
                del self.quotes[key]
                await self.quote_lock.acquire()
                self.save_quotes()
                self.quote_lock.release()
                return await self.message(mobj.channel, f"Quote {key} has been removed, you monster.")
            else:
                return await self.message(mobj.channel, "That key is not in the quote database.")
        elif len(args) == 1:
            key = args[0].lower()
            if key in self.quotes:
                value = self.quotes[key]
                embd = Embed(
                title = key,
                colour = Color(0x7289da)
                )
                embd.add_field(name=f"{value[0]}", value=f"{value[1]}")
                return await self.embed(mobj.channel, embd)
        else:
            return await self.message(mobj.channel, "Invalid arguments")
            

    async def process_message(self, message):
        if message.author.name == 'Arsenios': return
        await self.notification_lock.acquire()
        msg = message.content.lower()
        notifiers = set()
        if any(x in msg for x in self.notifications.keys()):
            for current, value in self.notifications.items():
                if current in msg:
                    notifiers |= value
        else:
            self.notification_lock.release()
            return
        self.notification_lock.release()
        if not notifiers: return
        await self.sleepers_lock.acquire()
        notifiers -= self.sleepers
        self.sleepers_lock.release()
        if notifiers: 
            for cur in notifiers:
                await self.message(cur, f"You have been mentioned in {message.channel.mention} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. The message was: \n\t```{message.author}: {message.content}```")
        #await self.message(message.channel, f"{', '.join(x.mention for x in notifiers)}")
        return
        
    @ChatBot.action('[String]')
    async def notify(self, args, mobj):
        """
        Adds you to a notification list on a word. Whenever the word is said in a message, you will be notified.
        """
        if len(args) < 1:
            return await self.message(mobj.channel, "Invalid Number of Arguments.")
        await self.notification_lock.acquire()
        self.notifications[" ".join(args).lower().strip()].add(mobj.author)
        self.save_notifications()
        self.notification_lock.release()
        return await self.message(mobj.channel, f"You have been added to be notified whenever '{' '.join(args).lower().strip()}' has been said.")
        
    @ChatBot.action('[Time (seconds)]')
    async def sleep(self, args, mobj):
        """
        Sleeps notifications for you for period of time in seconds. If the bot restarts (which it does every 2 hours), notification will be re-enabled then.
        """
        if len(args) != 1 or not args[0].isnumeric():
            return await self.message(mobj.channel, "Invalid Argument")
        await self.sleepers_lock.acquire()
        self.sleepers.add(mobj.author)
        self.sleepers_lock.release()
        await sleep(int(args[0]))
        await self.sleepers_lock.acquire()
        self.sleepers.remove(mobj.author)
        self.sleepers_lock.release()
        return
        
    @ChatBot.action('[String]')
    async def remove(self, args, mobj):
        """
        Removes notifications on keyword.
        """
        if len(args) < 1:
            return await self.message(mobj.channel, "Invalid Argument")
        await self.notification_lock.acquire()
        resp = " ".join(args).lower().strip()
        if resp in self.notifications:
            try:
                self.notifications[resp].remove(mobj.author)
            except:
                pass
        self.save_notifications()
        self.notification_lock.release()
        return await self.message(mobj.channel, f"You will stop being notified on {resp}")


            
        
if __name__ == "__main__":
    d = ArseniosBot("Arsenios")
    d.run()
    pass

# end
