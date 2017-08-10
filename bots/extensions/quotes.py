from Bot import ChatBot, Bot
import pickle
from asyncio import Lock, sleep
from discord import Embed, Color
from random import choice
from os.path import isfile, join
from pathlib import Path

class QUOTEBOT:

    def __init__(self, bot):
        self.bot = bot
        self.bot.quotes = self.load_quotes()
        self.bot.quote_lock = Lock()
        self.bot.save_quotes = self.save_quotes
    
    def load_quotes(self):
        """
        Loads quotes from quotes pickle file
        """
        if isfile(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.data')):
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.data'), 'rb')  as fp:
                quotes = pickle.load(fp)
                if not quotes:
                    quotes = {}
        else:
            self.bot.logger("There is no quotes file, creating.")
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.data'), 'wb')  as fp:
                quotes = {}
                pickle.dump(quotes, fp)
        return quotes
        
    def save_quotes(self):
        """
        Save quotes to quote pickle file.
        """
        with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.data'), 'wb')  as fp:
            pickle.dump(self.bot.quotes, fp)
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
        

        
        
        
def setup(bot):
    QUOTEBOT(bot)