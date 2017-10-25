from Bot import ChatBot
from discord import Embed, Color
from requests import get
from bs4 import BeautifulSoup as BS
from datetime import timedelta, datetime
from asyncio import ensure_future, sleep, Lock
import re
import feedparser
import pickle
from pathlib import Path
from os.path import isfile


class Item:
    dateadded = datetime(9999, 1, 1, 1, 1, 1)
    read = False
    old = False
    link = ""
    name = ""

    def __lt__(self, other):
        if self == other:
            return False
        if not self.read and other.read:
            return True
        if self.read and not other.read:
            return False
        if self.dateadded == other.dateadded:
            return self.name < other.name
        return self.dateadded < other.dateadded

    def __gt__(self, other):
        return not (self < other or self == other)

    def __hash__(self):
        return hash((self.link, self.dateadded))

    def __eq__(self, other):
        return self.dateadded == other.dateadded and self.link == other.link

    def __leq__(self, other):
        return self < other or self == other

    def __geq__(self, other):
        return self > other or self == other

    def isOld(self):
        self.old = (datetime.today() - self.dateadded) > timedelta(7)
        return self.old

    def isRead(self):
        return self.read

    def __init__(self, information):
        if "published_parsed" in information:
            if information["published_parsed"] is not None:
                self.dateadded = datetime(*information["published_parsed"][:6])
        if "updated_parsed" in information:
            if information["updated_parsed"] is not None:
                self.dateadded = datetime(*information["updated_parsed"][:6])
        if "link" in information:
            self.link = information["link"]  # .encode('utf8')
        try:
            self.name = information["title"]  # .encode('utf8')
            if self.name == "":
                self.name = self.link
        except BaseException:
            self.name = "Unknown Name"

    def get_link(self):
        return self.__link

    def get_name(self):
        return self.__name

    def __str__(self):
        return f"{self.name}\n\t{self.link}\n\t{self.dateadded}\n\t{'Read' if self.read else 'Unread'}"


class RSSBOT():
    def __init__(self, bot):
        self.bot = bot
        self.feeds = self.load_feeds()
        self.feedLock = Lock()
        self.bot.RSSaddInternal = self.addInternal
        self.bot.RSSremoveInternal = self.removeInternal
        self.bot.RSSlistInternal = self.listInternal
        """
        Of the format:
            {User: {url : {ignores:set, contain:set, read:list(Item)}}}
        """
        ensure_future(self.check())

    def load_feeds(self):
        """
        Loads rss settings from pickle file
        """
        if isfile(
            Path(
                self.bot.DATA_FOLDER,
                f'{self.bot.name}.rss')):
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.rss'), 'rb') as fp:
                notifications = pickle.load(fp)
                if not notifications:
                    notifications = {}
        else:
            self.bot.logger("There is no RSS file, creating.")
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.rss'), 'wb') as fp:
                notifications = {}
                pickle.dump(notifications, fp)

        return notifications

    def save_feeds(self):
        """
        Save rss settings to pickle file.
        """
        with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.rss'), 'wb') as fp:
            pickle.dump(self.feeds, fp)
        return

    async def check(self):
        await sleep(10)
        while(True):
            await self.feedLock.acquire()
            for user in self.feeds:
                a = [await self.runner(user, url, self.feeds[user][url], send=True) for url in self.feeds[user]]
            self.save_feeds()
            self.feedLock.release()
            await sleep(300)

    async def runner(self, user, input_url, readItems, send=True):

        url = f"https://nyaa.si/?page=rss&q={'+'.join(input_url)}&c=1_2&f=0"
        current = feedparser.parse(url)
        if not current.entries and current.bozo == 1:
            if "undefined entity" in str(current.bozo_exception):
                with urllib.request.urlopen(url) as req:
                    datum = req.read()
                    datum = datum.decode("utf-8", "ignore")
                    current = feedparser.parse(datum)
        feedItems = list(map(Item, current["items"]))

        unreadItems = self.update(feedItems, readItems)

        for item in unreadItems:
            if send:
                embed = Embed(
                    title=f"New RSS Item: {item.name}",
                    colour=Color(0x7289da),
                    url=f"{item.link}"
                )
                embed.add_field(name='Link', value=f"{item.link}")
                embed.add_field(name='Date', value=f"{item.dateadded}")
                await self.bot.embed(user, embed)
            item.read = True
        readItems.extend(unreadItems)
        return

    def update(self, feedItems, readItems):
        return [x for x in feedItems if not x.isOld() and x not in readItems]

    async def addInternal(self, args, mobj):
        await self.feedLock.acquire()
        user = mobj.author
        url = tuple(args)
        if user not in self.feeds:
            self.feeds[user] = {}
        self.feeds[user][url] = []
        await self.runner(user, url, self.feeds[user][url], send=False)
        self.save_feeds()
        self.feedLock.release()

    @ChatBot.action('[URL]')
    async def rssadd(self, args, mobj):
        """
        Adds a nyaa RSS search term feed to your tracker.

        The more specific you are, the more likely you are to get the ones that interest you.

        Example: !rssadd shokugeki horriblesubs s3 720p

        This will send you a private message when an item updates.
        """
        await self.RSSaddInternal(args, mobj)

        await self.message(mobj.channel, "You are now tracking that feed.")

    async def removeInternal(self, args, mobj):
        await self.feedLock.acquire()
        if mobj.author in self.feeds:
            if tuple(args) in self.feeds[mobj.author]:
                del self.feeds[mobj.author][tuple(args)]
        self.feedLock.release()
        await self.bot.message(mobj.author, f"Removed `{' '.join(args)}` from your tracker.")

    @ChatBot.action('[URL]')
    async def rssremove(self, args, mobj):
        """
        Removes an RSS feed from your tracker.
        """
        await self.RSSremoveInternal(args, mobj)

    async def listInternal(self, args, mobj):
        await self.feedLock.acquire()
        if mobj.author in self.feeds:
            if self.feeds[mobj.author]:
                await self.bot.message(mobj.author, 'You are tracking the following feeds:\n```{}```'.format("\n".join([" ".join(x) for x in self.feeds[mobj.author].keys()])))
            else:
                await self.bot.message(mobj.author, 'You are not tracking anything.')
        else:
            await self.bot.message(mobj.author, 'You are not tracking anything.')
        self.feedLock.release()

    @ChatBot.action()
    async def rsslist(self, args, mobj):
        """
        List feeds that you're subscribed to
        """
        await self.RSSlistInternal(args, mobj)


def setup(bot):
    RSSBOT(bot)
