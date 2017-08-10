
from pyanimelist import PyAnimeList
from Bot import ChatBot, Bot
from discord import Embed, Color
from json import load as jload
from pathlib import Path
from utils import unescape

class MALBOT:
    
    def __init__(self, bot):
        self.bot = bot
        user, password = self.read_mal(self.bot)
        self.bot.pyanimelist = PyAnimeList(username=user, password=password, user_agent="Arsenios_Bot")
    
    @staticmethod
    def read_mal(bot):
        """
        Read a bot's key JSON to get it's token/webhook link
        Keys must be stored in the key folder and have a basic 'key':'<keytext>' object
        """
        with open(Path(bot.KEY_FOLDER, f'{bot.name}.key'), 'r') as f:
            datum = jload(f)
            user = datum.get("user", "")
            password = datum.get("password", "")
            if not (user or password):
                raise IOError("Key not found in JSON keyfile")
            return user, password
        return None


        
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
        embed.add_field(name="Dates", value=f'{anime.start_date} through {anime.end_date if anime.end_date != "0000-00-00" else "present"}' if anime.start_date != anime.end_date else f'{anime.start_date}')
        embed.add_field(name="Synopsis", value=unescape(anime.synopsis).split("\n\n", maxsplit=1)[0])

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
        embed.add_field(name="Length", value=f'{manga.chapters} Chapters, {manga.volumes} Volumes')
        embed.add_field(name="Type", value=manga.type)
        embed.add_field(name="Status", value=manga.status)
        embed.add_field(name="Dates", value=f'{manga.start_date} through {manga.end_date if manga.end_date != "0000-00-00" else "present"}' if manga.start_date != manga.end_date else f'{manga.start_date}')
        embed.add_field(name="Synopsis", value=unescape(manga.synopsis).split("\n\n", maxsplit=1)[0])

        await self.embed(mobj.channel, embed) 
        
def setup(bot):
    MALBOT(bot)