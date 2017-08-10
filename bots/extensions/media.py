from Bot import ChatBot, Bot
from discord import Embed, Color
from requests import get
from bs4 import BeautifulSoup as BS

class MEDIABOT():
    def __init__(self, bot):
        self.bot = bot

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
        resp = get(f"{tube}/?q={self.replace(' '.join(args))}&f=0&c=1_2&s=id&o=desc")
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
                locator = 0
                for i,current in enumerate(hrefs[1:]):
                    if "title" in current.attrs and 'comments' in current['href']:
                        continue
                    locator = i
                    break
                link = f"{tube}{hrefs[1+locator]['href']}"
                the_title = f"{hrefs[1+locator]['title']}"
                if find_horrible:
                    if "HorribleSubs" not in the_title: continue
                seeds = int(container.find("td", style="color: green;").text)
                if not seeds: continue
                leechers = int(container.find("td", style="color: red;").text)
                date=container.find("td", attrs={"data-timestamp":True}).text
                if "magnet" in hrefs[2+locator]['href']:
                    magnet = hrefs[2+locator]['href']
                    torrent= None
                else:
                    torrent = f"https://nyaa.si/{hrefs[2+locator]['href']}"
                    magnet = hrefs[3+locator]['href']
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
                embd.add_field(name="Uploaded", value=f"{date}")
                embd.add_field(name="More Results", value=f"[Search]({tube}/?q={self.replace('%20'.join(args))}&f=0&c=1_2&s=id&o=desc)")
                return await self.embed(mobj.channel, embd)     
            
        return await self.message(mobj.channel, "No Torrents with seeders found")
        
def setup(bot):
    MEDIABOT(bot)