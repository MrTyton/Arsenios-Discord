#!/usr/bin/env python
#-*- coding: utf-8 -*-

from random import randint, choice
from Bot import ChatBot, Bot
from requests import get
from bs4 import BeautifulSoup as BS
from discord import Embed, Color
from pyanimelist import PyAnimeList
from json import load as jload
from pathlib import Path
from os import listdir
from os.path import isfile, join
from random import choice
import pickle
from mtgsdk import Card
from asyncio import Lock, sleep
from collections import defaultdict
from datetime import datetime

class ArseniosBot(ChatBot):
    """
    Dumb Bot is a basic toy bot integration
    He has some built in functionality as well as webhook-bot
    integrations to provide a connection to webhooks

    WebHook data is stored in the 'shared' folder, so we
    allow Dumb Bot to access the shared pool
    """

    STATUS = "I'm a bot, Beep Bloop!"
    def read_mal(self):
        """
        Read a bot's key JSON to get it's token/webhook link
        Keys must be stored in the key folder and have a basic 'key':'<keytext>' object
        """
        with open(Path(self.KEY_FOLDER, f'{self.name}.key'), 'r') as f:
            datum = jload(f)
            user = datum.get("user", "")
            password = datum.get("password", "")
            if not (user or password):
                raise IOError("Key not found in JSON keyfile")
            return user, password
        return None
        
    def load_quotes(self):
        """
        Loads quotes from quotes pickle file
        """
        with open(Path(self.DATA_FOLDER, f'{self.name}.data'), 'rb')  as fp:
            quotes = pickle.load(fp)
            if not quotes:
                quotes = {}
            return quotes
            
    def load_notifications(self):
        """
        Loads notification settings from pickle file
        """
        with open(Path(self.DATA_FOLDER, f'{self.name}.notifications'), 'rb') as fp:
            notifications = pickle.load(fp)
            if not notifications:
                notifications = defaultdict(set)
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
    
            
            
    # Used to convert chars to emojis for /roll
    emojis = {f"{i}":x for i, x in enumerate([f":{x}:" for x in
        ("zero", "one", "two", "three", "four", 
         "five", "six", "seven", "eight", "nine")])}

    def __init__(self, name):
        super(ArseniosBot, self).__init__(name)
        self.filegen = self._create_filegen("shared")
        user, password = self.read_mal()
        self.pyanimelist = PyAnimeList(username=user, password=password, user_agent="Arsenios_Bot")
        self.quotes = self.load_quotes()
        self.quote_lock = Lock()
        self.notifications = self.load_notifications()
        self.notification_lock = Lock()
        self.sleepers = set()
        self.sleepers_lock = Lock()
        self.create_reactions()
        
        
    @ChatBot.action("[String]")
    async def anime(self, args, mobj):
    
        """
        Does a MAL search to find requested anime. If there is more than 1 option, will ask up to the first 15 choices. You have 10 seconds to respond.
        """
    
        author = mobj.author
        try:
            animes = await self.pyanimelist.search_all_anime(f"{' '.join(args)}")
        except:
            return await self.message(mobj.channel, "Cannot find anything")
        
        animes_ = dict(enumerate(animes[:15]))
        if len(animes_) > 1:
            message = "```What anime would you like:\n"
            for anime in animes_.items():
          
                message += "[{}] {}\n".format(str(anime[0]+1), anime[1].title)
            
            message += "\nUse the number to the side of the anime as a key to select it!```"

            
            await self.message(mobj.channel, message)

            msg = await self.client.wait_for_message(timeout=10.0, author=author)
            
            if not msg: return
            
            key = int(msg.content)-1
        else:
            key = 0
        try:
            anime = animes_[key]
        except (ValueError, KeyError):
            return await self.message(mobj.channel, "Invalid key.")
        
        embed = Embed(
            title=anime.title,
            colour=Color(0x7289da),
            url="https://myanimelist.net/anime/{0.id}/{0.title}".format(anime).replace(" ", "%20")
        )
        #embed.set_author(name=author.display_name, icon_url=avatar)
        embed.set_image(url=anime.image)
        embed.add_field(name="Episode Count", value=str(anime.episodes))
        embed.add_field(name="Type", value=anime.type)
        embed.add_field(name="Status", value=anime.status)
        embed.add_field(name="Dates", value=f'{anime.start_date} through {anime.end_date}' if anime.start_date != anime.end_date else f'{anime.start_date}')
        embed.add_field(name="Synopsis", value=anime.synopsis.split("\n\n", maxsplit=1)[0])

        await self.embed(mobj.channel, embed)
        
    @ChatBot.action("[String]")
    async def manga(self, args, mobj):
    
        """
        Does a MAL search to find requested manga. If there is more than 1 option, will ask up to the first 15 choices. You have 10 seconds to respond.
        """
    
        author = mobj.author
        try:
            mangas = await self.pyanimelist.search_all_manga(f"{' '.join(args)}")
        except:
            return await self.message(mobj.channel, "Cannot find anything")
            
        mangas_ = dict(enumerate(mangas[:15]))
        if len(mangas_) > 1:
            message = "```What manga would you like:\n"
            for manga in mangas_.items():
          
                message += "[{}] {}\n".format(str(manga[0]+1), manga[1].title)
            
            message += "\nUse the number to the side of the manga as a key to select it!```"

            
            await self.message(mobj.channel, message)

            msg = await self.client.wait_for_message(timeout=10.0, author=author)
            
            if not msg: return
            
            key = int(msg.content)-1
        else:
            key = 0
        try:
            manga = mangas_[key]
        except (ValueError, KeyError):
            return await self.message(mobj.channel, "Invalid key.")
        
        embed = Embed(
            title=manga.title,
            colour=Color(0x7289da),
            url="https://myanimelist.net/manga/{0.id}/{0.title}".format(manga).replace(" ", "%20")
        )
        #embed.set_author(name=author.display_name, icon_url=avatar)
        embed.set_image(url=manga.image)
        embed.add_field(name="Volume Count", value=str(manga.volumes))
        embed.add_field(name="Type", value=manga.type)
        embed.add_field(name="Status", value=manga.status)
        embed.add_field(name="Dates", value=f'{manga.start_date} through {manga.end_date}' if manga.start_date != manga.end_date else f'{manga.start_date}')
        embed.add_field(name="Synopsis", value=manga.synopsis.split("\n\n", maxsplit=1)[0])

        await self.embed(mobj.channel, embed) 
    
    @ChatBot.action('[Card Name]')
    async def card(self, args, mobj):
    
        """
        Does a search for requested magic card.
        If there are multiple cards with similar name, will prompt to select one.
        """
        author = mobj.author
        try:
            cards = Card.where(name=" ".join(args)).all()
        except:
            return await self.message(mobj.channel, "Something broke when requesting cards.")
        
        cards_ = dict()
        entered = []
        a = 0
        for cur in cards:
            if cur.name not in entered:
                cards_[a] = cur
                a += 1
                entered.append(cur.name)
                if len(entered) > 15: break
        if len(cards_) == 0:
            return await self.message(mobj.channel, "No cards found.")
        if len(cards_) > 1:
            message = "```What card would you like:\n"
            for anime in cards_.items():
          
                message += "[{}] {}\n".format(str(anime[0]+1), anime[1].name)
            
            message += "\nUse the number to the side of the name as a key to select it!```"

            
            await self.message(mobj.channel, message)

            msg = await self.client.wait_for_message(timeout=10.0, author=author)
            
            if not msg: return
            
            key = int(msg.content)-1
        else:
            key = 0
            
        try:
            card = cards_[key]
        except (ValueError, KeyError):
            return await self.message(mobj.channel, "Invalid key.")
        embd = Embed(
            title=card.name,
            colour=Color(0x7289da),
            url=f"http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={card.multiverse_id}"
        )
        if card.colors:
            embd.add_field(name="Color", value=f'{", ".join(card.colors)}')
        else:
            embd.add_field(name="Color", value=f'Colorless')
        if card.mana_cost:
            embd.add_field(name="Mana Cost", value=card.mana_cost)
            embd.add_field(name="CMC", value=card.cmc)
        last_set = card.printings[-1]
        embd.add_field(name="Last Printing", value=last_set)
        if len(card.printings) > 1:
            embd.add_field(name="Other Printings", value=f"{', '.join([x for x in card.printings if x != last_set])}")
        

        legalities = {x["format"]:f'{x["format"]}: {x["legality"]}' for x in card.legalities if x['legality'] == 'Banned' or x['legality'] == 'Restricted'}
        for format in ["Standard", "Modern", "Legacy", "Vintage"]:
            if format in [x["format"] for x in card.legalities]:
                legalities[format] = [f'{q["format"]}: {q["legality"]}' for q in card.legalities if q["format"] == format][0]
        embd.add_field(name="Legality", value='\n'.join(legalities.values()))
        embd.add_field(name="Type", value=card.type)
        if card.supertypes:
            embd.add_field(name="Supertypers", value=card.supertypes)
        if card.subtypes:
            embd.add_field(name="Subtypes", value=f"{', '.join(card.subtypes)}")
        if 'creature' in card.type:
            embd.add_field(name="Power/Toughness", value=f"{card.power}/{card.toughness}")
        if 'planeswalker' in card.type:
            embd.add_field(name="Loyalty", value=card.loyalty)
        if card.text:
            embd.add_field(name="Card Text", value=card.text)
        latest_picture = Card.where(name=card.name, set=last_set).all()[0]
        embd.set_image(url=latest_picture.image_url)
        
        return await self.embed(mobj.channel, embd)
        
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

    
        
    @ChatBot.action()
    async def coin(self, args, mobj):
        """
        Do a coin flip
        Example: !coin
        """
        return await self.message(mobj.channel, choice([":monkey:", ":peach:"]))
        
    @ChatBot.action("<String>")
    async def will(self, args, mobj):
        """
        Asks the magic 8-bot a question, and recieve a response
        """
        if not args: return await self.message(mobj.channel, "Question is hazy, please try again.")
        answers = ["It is certain",'It is decidedly so','Without a doubt','Yes definitely','You may rely on it','As I see it, yes','Most likely','Outlook good','Yes','Signs point to yes','Reply hazy try again','Ask again later','Better not tell you now','Cannot predict now','Concentrate and ask again',"Don't count on it",'My reply is no','My sources say no','Outlook not so good','Very doubtful']
        
        return await self.message(mobj.channel, choice(answers))


    @ChatBot.action('[Number]|[Number d Number]')
    async def roll(self, args, mobj):
        """
        1) Make a roll between [1..1000]
        Example: !roll 100
        2) Roll XdY [max 100 dice, max 1000 sides. If you choose too large options then it might not print the result.]
        Example: !roll 3d6
        """
        if not args or len(args) > 1:
            return await self.message(mobj.channel, "Invalid arg count")

        x, = args
        if x == "barrel":
            return await self.message(mobj.channel, "https://www.youtube.com/watch?v=mv5qzMtLE60")
        if 'd' in x:
            dice, sides = x.split("d")
            ans = []
            if not dice.isnumeric() or not sides.isnumeric():
                return await self.message(mobj.channel, "Non-numeric args given.")
            if int(dice) > 100 or int(dice) < 1 or int(sides) > 1000 or int(sides) < 1:
                return await self.message(mobj.channel, "Invalid Argument Range")
            for i in range(int(dice)):
                ans.append(randint(1, int(sides)))
            summation = sum(ans)
            res = "+".join(["".join(self.emojis[x] for x in str(y).zfill(len(str(y)))) for y in ans]) + "=" + "".join([self.emojis[x] for x in str(summation).zfill(len(str(summation)))])
        else:
            if not x.isnumeric():
                return await self.message(mobj.channel, "Non-numeric arg given")

            num = int(x) # bad 
            if num < 1 or num > 1000:
                return await self.message(mobj.channel, "Invalid range given")

            res = [self.emojis[x] for x in str(randint(1, num)).zfill(len(x))]
        return await self.message(mobj.channel, "".join(res))

    @ChatBot.action('[Search terms]')
    async def yt(self, args, mobj):
        """
        Get the first Youtube search result video
        Example: !yt how do I take a screenshot
        """
        if not args:
            return await self.message(mobj.channel, "Empty search terms")
        
        tube = "https://www.youtube.com"
        resp = get(f"{tube}/results?search_query={self.replace(' '.join(args))}")
        if resp.status_code != 200:
            return await self.message(mobj.channel, "Failed to retrieve search")

        # Build a BS parser and find all Youtube links on the page
        bs = BS(resp.text, "html.parser")
        main_d = bs.find('div', id='results')
        if not main_d:
            return await self.message(mobj.channel, 'Failed to find results')

        items = main_d.find_all("div", class_="yt-lockup-content")
        if not items:
            return await self.message(mobj.channel, "No videos found")

        # Loop until we find a valid non-advertisement link
        for container in items:
            href = container.find('a', class_='yt-uix-sessionlink')['href']
            if href.startswith('/watch'):
                return await self.message(mobj.channel, f'{tube}{href}')        
        return await self.message(mobj.channel, "No YouTube video found")
        
        
    @ChatBot.action('[Search terms]')
    async def nyaa(self, args, mobj):
        """
        Get the first nyaa search result where there are seeders
        Example: !nyaa horriblesubs boruto 01
        """
        if not args:
            return await self.message(mobj.channel, "Empty search terms")
        
        tube = "https://www.nyaa.si"
        resp = get(f"{tube}/?q={self.replace(' '.join(args))}&f=0&c=1_2")
        if resp.status_code != 200:
            return await self.message(mobj.channel, "Failed to retrieve search")

        # Build a BS parser and find all Nyaa links on the page
        bs = BS(resp.text, "html.parser")
        main_d = bs.find('tbody')
        if not main_d:
            return await self.message(mobj.channel, 'Failed to find results')

        items = main_d.find_all("tr", {'class':['danger', 'success', 'default']})
        if not items:
            return await self.message(mobj.channel, "Failed to find results")

        # Loop until we find a valid non-advertisement link
        for find_horrible in [True, False]:
            for container in items:
                hrefs = container.find_all('a')
                link = f"{tube}{hrefs[1]['href']}"
                the_title = f"{hrefs[1]['title']}"
                if find_horrible:
                    if "HorribleSubs" not in the_title: continue
                seeds = int(container.find("td", style="color: green;").text)
                if not seeds: continue
                leechers = int(container.find("td", style="color: red;").text)
                if "magnet" in hrefs[2]['href']:
                    magnet = hrefs[2]['href']
                    torrent= None
                else:
                    torrent = hrefs[2]['href']
                    magnet = hrefs[3]['href']
                embd = Embed(
                    title=the_title,
                    color=Color(0x7289da),
                    url=f"{link}",
                )
                if torrent:
                    link_string = f"[Magnet]({magnet}), [Torrent]({torrent})"
                else:
                    link_string = f"[Magnet]({magnet})"
                embd.add_field(name="Links", value=link_string)
                embd.add_field(name="Status", value=f"{seeds} seeders, {leechers} leechers")
                embd.add_field(name="More Results", value=f"[Search]({tube}/?q={self.replace('%20'.join(args))}&f=0&c=1_2)")
                return await self.embed(mobj.channel, embd)     
            
        return await self.message(mobj.channel, "No Torrents with seeders found")
        
    
    @ChatBot.action('[String]')
    async def spam(self, args, mobj):
        """
        Spam a channel with dumb things
        Example: !spam :ok_hand:
        """
        if not args or len(args) > 10:
            return await self.message(mobj.channel, "Invalid spam input")
        y = args * randint(5, 20)
        return await self.message(mobj.channel, f"{' '.join(y)}")


    @ChatBot.action('<Poll Query>')
    async def poll(self, args, mobj):
        """
        Turn a message into a 'poll' with up/down thumbs
        Example: !poll should polling be a feature?
        """
        await self.client.add_reaction(mobj, '👍')
        await self.client.add_reaction(mobj, '👎')
        return
    

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
