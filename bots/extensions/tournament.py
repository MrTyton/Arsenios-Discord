from Bot import ChatBot, Bot
from discord import Embed, Color
from requests import get
from bs4 import BeautifulSoup as BS

from datetime import date
from pickle import load, dump

import inflect

from asyncio import ensure_future, sleep, Lock

from pathlib import Path
from os.path import isfile, join

class TOURNAMENTBOT:

    def __init__(self, bot):
        self.bot = bot
        self.bot.add_player = self.add_player
        self.bot.add_tournament = self.add_tournament
        self.ordinalize = inflect.engine().ordinal
        self.tournament_lock = Lock()
        ensure_future(self.check())
        


    async def load_tournaments(self):
        """
        Loads tournaments from data folder
        """
        
        if isfile(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.tournaments')):
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.tournaments'), 'rb')  as fp:
                tournament = load(fp)
                if not tournament:
                    tournamnet = {}
        else:
            self.bot.logger("There is no tournament file, creating.")
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.tournaments'), 'wb')  as fp:
                tournament = {}
                dump(tournament, fp)
        return tournament

    async def save_tournaments(self, tournaments):
        with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.tournaments'), 'wb')  as fp:
            dump(tournaments, fp)
        
    async def add_tournament(self, url, name, chan):
        info = {}
        info['url'] = url
        info['round'] = 1
        info['players'] = set()
        info['title'] = name
        info['channel'] = chan
        await self.tournament_lock.acquire()
        tournaments = await self.load_tournaments()
        namestring = f"{name} {chan.id}"
        if namestring in tournaments:
            self.tournament_lock.release()
            raise ValueError("Tournament name is already taken in this channel")
        tournaments[f"{name} {chan.id}"] = info
        await self.save_tournaments(tournaments)
        self.tournament_lock.release()
        
    async def add_player(self, chan, title, name):
        await self.tournament_lock.acquire()
        tournaments = await self.load_tournaments()
        if f"{title} {chan.id}" not in tournaments:
            self.tournament_lock.release()
            raise ValueError("Tournament ID is not being tracked")
        tournaments[f"{title} {chan.id}"]['players'].add(name)
        await self.save_tournaments(tournaments)
        self.tournament_lock.release()
        
    @ChatBot.action('[Tournament Base URL] [Name]')
    async def tournament(self, args, mobj):
        """
        Starts tracking a tournament. Base url is of the form (event page links)
            Wizards of the Coast:
                http://magic.wizards.com/en/events/coverage/[CHANGETHISPART]/
            Starcity Games (only for main event):
                http://www.starcitygames.com/events/[CHANGETHISPARTHERE].html
        Name is one word.
        Exampe:
            !tournament http://magic.wizards.com/en/events/coverage/gpdc/ GPDC
            !tournament http://www.starcitygames.com/events/160917_louisville.html SCG_Louisville
        """
        try:
            await self.add_tournament(args[0], args[1], mobj.channel)
        except Exception as e:
            return await self.message(mobj.channel, f"{e}")
        
    @ChatBot.action('[Tournament Name] [Player]')
    async def track(self, args, mobj):
        """
        Tracks a player in the specified tournament.
        Example:
            !track GPDC Sukenik
        """
        try:
            await self.add_player(mobj.channel, args[0], f"{' '.join(args[1:]).strip()}")
        except Exception as e:
            return await self.message(mobj.channel, f"{e}")
        return await self.message(mobj.channel, "Player is now being tracked.")
    

            
        
    async def check(self):
        """
        Sleeper thread. Checks every 5 minutes for tournament updates and then posts them to the respective channels.
        """
        await sleep(5)
        while(True):
            await self.tournament_lock.acquire()
            tournaments = await self.load_tournaments()   
            removals = []
            for named_tourny in tournaments:
                cur = tournaments[named_tourny]
                url = self.generate_url(cur['url'], cur['round'])
                if not url:
                    continue
                parsed_page = self.parse_url(url, cur['players'])
                if parsed_page == []:
                    cur['round'] += 1
                    if cur['round'] == 16: removals.append(named_tourny)
                    continue
                elif parsed_page == None:
                    continue
                parsed_players = self.parse_players(parsed_page, cur['round'])
                
                if parsed_players == {}:
                    cur['round'] += 1
                    if cur['round'] == 16: removals.append(named_tourny)
                    continue
                    
                embed = Embed(
                    title=f"{cur['title']} Round {cur['round']}",
                    colour=Color(0x7289da),
                )
                
                for playa, nfo in sorted(parsed_players.items(), key = lambda x : x[1]['place']):
                    embed.add_field(name=playa, value=f"In {self.ordinalize(nfo['place'])} place with a record of {nfo['record']}", inline=False)
                    
                await self.bot.embed(cur['channel'], embed)
                
                cur['round'] += 1                
                if cur['round'] == 16: removals.append(named_tourny)
            
            for deletion in removals:
                del tournaments[deletion]
            
            await self.save_tournaments(tournaments)
            self.tournament_lock.release()
            
            await sleep(300)
                
    
        
    def parse_url(self, url, player_list):
        """
        Parses the provided url to get the player objects.
        """        
        resp = get(url)
        if resp.status_code != 200:
            return None
        bs = BS(resp.text, 'html.parser')
        tags = bs.find_all('tr')
        players = [x for x in tags if any([y in x.text for y in player_list])]
        return players
        
    def calculate_score(self, score, round):
        """
        Calculates the record of the player. Assumations are that a player will not have more than 2 draws, as having 3 draws is the same as having 2 losses.
        """        
        score = int(score)
        max_wins = score // 3
        max_draws = score - (max_wins * 3)
        max_losses = round - max_wins - max_draws
        return f"{max_wins}-{max_losses}-{max_draws}"
        
    def parse_players(self, players, current_round):
        ans_dict = {}
        for cur in players:
            player_dict = {}
            fields = cur.find_all('td')
            player_dict['place'] = int(fields[0].get_text())
            player_dict['points'] = int(fields[2].get_text())
            player_dict['record'] = self.calculate_score(player_dict['points'], current_round)
            ans_dict[fields[1].get_text()] = player_dict
        return ans_dict
        
    def generate_url(self, base, current_round): #should modify this to take into account that there are classics. This right now should only get the first tournament.
        if "wizards" in base:
            d = date.today()
            url = f"http://magic.wizards.com/en/events/coverage/gpdc/round-{current_round}-standings-{d.strftime('%Y-%m-%d')}"
        if "starcity" in base:
            resp = get(base)
            if resp.status_code != 200:
                return None
            bs = BS(resp.text, 'html.parser')
            table = bs.find('table', {"class":"standings_table"})
            rows = table.find_all('tr')
            url = [x.find_all('td')[2].find('a')['href'] for x in rows if x.find_all('td')[2].text == str(current_round)]
            if url == []:
                return None
            url = url[0]
        return url

        
def setup(bot):
    TOURNAMENTBOT(bot)