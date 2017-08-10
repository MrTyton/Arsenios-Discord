
from Bot import ChatBot, Bot
from discord import Embed, Color
from pathlib import Path
from os.path import isfile, join
import pickle
from asyncio import Lock, sleep
from collections import defaultdict
from datetime import datetime


class NOTIFYBOT:
    
    def __init__(self, bot):
        self.bot = bot
        
        self.bot.notifications = self.load_notifications()
        self.bot.notification_lock = Lock()
        self.bot.sleepers = set()
        self.bot.sleepers_lock = Lock()
        self.bot.process_message = self.process_message
        
    def load_notifications(self):
        """
        Loads notification settings from pickle file
        """
        if isfile(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.notifications')):
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.notifications'), 'rb') as fp:
                notifications = pickle.load(fp)
                if not notifications:
                    notifications = defaultdict(set)
        else:
            self.bot.logger("There is no notification file, creating.")
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.notifications'), 'wb') as fp:
                notifications = defaultdict(set)
                pickle.dump(notifications, fp)
                
        return notifications
            
    def save_notifications(self):
        """
        Save notification settings to pickle file.
        """
        with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.notifications'), 'wb')  as fp:
            pickle.dump(self.bot.notifications, fp)
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
        
    async def process_message(self, message):
        if message.author.name == 'Arsenios': return
        await self.bot.notification_lock.acquire()
        msg = message.content.lower()
        notifiers = set()
        if any(x in msg for x in self.bot.notifications.keys()):
            for current, value in self.bot.notifications.items():
                if current in msg:
                    notifiers |= value
        else:
            self.bot.notification_lock.release()
            return
        self.bot.notification_lock.release()
        if not notifiers: return
        await self.bot.sleepers_lock.acquire()
        notifiers -= self.bot.sleepers
        self.bot.sleepers_lock.release()
        if notifiers: 
            for cur in notifiers:
                await self.bot.message(cur, f"You have been mentioned in {message.channel.mention} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. The message was: \n\t```{message.author}: {message.content}```")
        #await self.bot.message(message.channel, f"{', '.join(x.mention for x in notifiers)}")
        return
        
        
        
        
        
        
        
def setup(bot):
    NOTIFYBOT(bot)