from Bot import ChatBot
import pickle
from asyncio import Lock
from discord import Embed, Color
from os.path import isfile
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
        if isfile(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.quotes')):
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.quotes'), 'rb') as fp:
                quotes = pickle.load(fp)
                if not quotes:
                    quotes = {}
        else:
            self.bot.logger("There is no quotes file, creating.")
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.quotes'), 'wb') as fp:
                quotes = {}
                pickle.dump(quotes, fp)
        return quotes

    def save_quotes(self):
        """
        Save quotes to quote pickle file.
        """
        with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.quotes'), 'wb') as fp:
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
        if mobj.server.id not in self.quotes:
            self.quotes[mobj.server.id] = {}
        server_quotes = self.quotes[mobj.server.id]
        if len(args) == 0:
            if len(server_quotes) == 0:
                return await self.error(mobj.channel, "No quotes in the database")
            embd = Embed(
                title="List of Options",
                colour=Color(0x7289da)
            )

            value = "\n".join(server_quotes.keys())
            embd.add_field(name=f"List", value=value)
            return await self.embed(mobj.channel, embd)
        elif args[0].lower() == "add" and len(args) > 2:
            key = args[1].lower()
            if key in server_quotes:
                return await self.error(mobj.channel, "Key is already in quotes database.")
            value = [mobj.author, " ".join(args[2:]).strip()]
            server_quotes[key] = value
            await self.quote_lock.acquire()
            self.save_quotes()
            self.quote_lock.release()
            return await self.message(mobj.channel, f"Added quote {key}.")
        elif args[0].lower() == "remove" and len(args) == 2:
            key = args[1].lower()
            if key in server_quotes:
                del server_quotes[key]
                await self.quote_lock.acquire()
                self.save_quotes()
                self.quote_lock.release()
                return await self.message(mobj.channel, f"Quote {key} has been removed, you monster.")
            else:
                return await self.error(mobj.channel, "That key is not in the quote database.")
        elif len(args) == 1:
            key = args[0].lower()
            if key in server_quotes:
                value = server_quotes[key]
                embd = Embed(
                    title=key,
                    colour=Color(0x7289da)
                )
                embd.add_field(name=f"{value[0]}", value=f"{value[1]}")
                return await self.embed(mobj.channel, embd)
        else:
            return await self.error(mobj.channel, "Invalid arguments")


def setup(bot):
    QUOTEBOT(bot)
