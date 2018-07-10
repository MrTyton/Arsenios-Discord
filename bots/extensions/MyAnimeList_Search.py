
from pyanimelist import PyAnimeList
from Bot import ChatBot
from discord import Embed, Color
from json import load as jload
from pathlib import Path
from utils import unescape
from google import google


class MALBOT:

    def __init__(self, bot):
        self.bot = bot
        user, password = self.read_mal()
        self.pyanimelist = PyAnimeList(
            username=user,
            password=password,
            user_agent="Arsenios_Bot"
        )
        self.pylist_options = {
            'anime': self.pyanimelist.search_all_anime,
            'manga': self.pyanimelist.search_all_manga}
        self.bot.mal_get_options = self.get_options

    def read_mal(self):
        """
        Read a bot's key JSON to get it's token/webhook link
        Keys must be stored in the key folder and have a basic 'key':'<keytext>' object
        """
        with open(Path(self.bot.KEY_FOLDER, f'{self.bot.name}.key'), 'r') as f:
            datum = jload(f)
            user = datum.get("user", "")
            password = datum.get("password", "")
            if not (user or password):
                raise IOError("Key not found in JSON keyfile")
            return user, password
        return None

    async def get_options(self, type, search, mobj, recur=False):
        author = mobj.author
        try:
            results = await self.pylist_options[type](f"{' '.join(search)}")
            if len(results) == 0:
                raise BaseException("Not returning anything?")
        except BaseException as e:
            print(e)
            if not recur:
                await self.bot.message(mobj.channel, "Cannot find anything, performing google search to check for mispellings...")
                mispell = google.search(f"site:myanimelist.net {' '.join(search)} {type}", 1)
                if mispell:
                    return await self.get_options(type, mispell[0].link.split("/")[-1].split("_"), mobj, recur=True)
            await self.bot.error(mobj.channel, "Could not find anything.")
            return None

        results_ = dict(enumerate(results[:15]))
        if len(results_) == 0:
            await self.bot.error(mobj.channel, "Could not find anything.")
            return None
        if len(results_) > 1:
            message = "```What {} would you like:\n".format(type)
            for result in results_.items():

                message += "[{}] {}\n".format(str(result[0] + 1),
                                              result[1].title)

            message += "\nUse the number to the side of the {} as a key to select it!```".format(
                type)

            await self.bot.message(mobj.channel, message)

            msg = await self.bot.client.wait_for_message(timeout=10.0, author=author)

            if not msg:
                await self.bot.error(mobj.channel, "Operation has timed out, please try again.")
                return None

            key = int(msg.content) - 1
        else:
            key = 0
        try:
            result = results_[key]
        except (ValueError, KeyError):
            await self.bot.error(mobj.channel, "Invalid key.")
            return None
        return result

    @ChatBot.action("[String]")
    async def anime(self, args, mobj):

        """
        Does a MAL search to find requested anime. If there is more than 1 option, will ask up to the first 15 choices. You have 10 seconds to respond.
        """
        print(args)
        anime = await self.mal_get_options('anime', args, mobj)

        if not anime:
            return

        embed = Embed(
            title=anime.title,
            colour=Color(0x7289da),
            url="https://myanimelist.net/anime/{0.id}/{0.title}".format(anime).replace(" ", "%20")
        )
        embed.set_image(url=anime.image)
        embed.add_field(name="Episode Count", value=str(anime.episodes))
        embed.add_field(name="Type", value=anime.type)
        embed.add_field(name="Status", value=anime.status)
        embed.add_field(
            name="Dates",
            value=f'{anime.start_date} through {anime.end_date if anime.end_date != "0000-00-00" else "present"}' if anime.start_date != anime.end_date else f'{anime.start_date}')
        anime.synopsis = unescape(
            anime.synopsis).split(
            "\n\n",
                maxsplit=1)[0]
        if len(anime.synopsis) > 1000:
            if "\n" in anime.synopsis[:965]:
                anime.synopsis = anime.synopsis[:anime.synopsis[:965].rfind(
                    "\n")]
            else:
                anime.synopsis = anime.synopsis[:965]
            anime.synopsis += "\nIncomplete synopsis due to length."
        embed.add_field(
            name="Synopsis",
            value=anime.synopsis)
        try:
            await self.embed(mobj.channel, embed)
        except BaseException:
            await self.error(mobj.channel, "Something when trying to format the object. Here is a link to the anime: " + "https://myanimelist.net/anime/{0.id}/{0.title}".format(anime).replace(" ", "%20"))

    @ChatBot.action("[String]")
    async def manga(self, args, mobj):

        """
        Does a MAL search to find requested manga. If there is more than 1 option, will ask up to the first 15 choices. You have 10 seconds to respond.
        """

        manga = await self.mal_get_options('manga', args, mobj)

        if not manga:
            return

        embed = Embed(
            title=manga.title,
            colour=Color(0x7289da),
            url="https://myanimelist.net/manga/{0.id}/{0.title}".format(manga).replace(" ", "%20")
        )
        # embed.set_author(name=author.display_name, icon_url=avatar)
        embed.set_image(url=manga.image)
        embed.add_field(
            name="Length",
            value=f'{manga.chapters} Chapters, {manga.volumes} Volumes')
        embed.add_field(name="Type", value=manga.type)
        embed.add_field(name="Status", value=manga.status)
        embed.add_field(
            name="Dates",
            value=f'{manga.start_date} through {manga.end_date if manga.end_date != "0000-00-00" else "present"}' if manga.start_date != manga.end_date else f'{manga.start_date}')
        manga.synopsis = unescape(
            manga.synopsis).split(
            "\n\n",
                maxsplit=1)[0]
        if len(manga.synopsis) > 1000:
            if "\n" in manga.synopsis[:965]:
                manga.synopsis = manga.synopsis[:manga.synopsis[:965].rfind(
                    "\n")]
            else:
                manga.synopsis = manga.synopsis[:965]
            manga.synopsis += "\nIncomplete synopsis due to length."

        embed.add_field(
            name="Synopsis",
            value=manga.synopsis)

        try:
            await self.embed(mobj.channel, embed)
        except BaseException:
            await self.error(mobj.channel, "Something when trying to format the object. Here is a link to the manga: " + "https://myanimelist.net/manga/{0.id}/{0.title}".format(manga).replace(" ", "%20"))


def setup(bot):
    MALBOT(bot)
