from Bot import ChatBot
from discord import Embed, Color
from html import unescape
import requests
import difflib
import traceback
import re
import sys, os
import warnings
with warnings.catch_warnings():
    warnings.filterwarnings("ignore", category=UserWarning)
    from fuzzywuzzy import fuzz
from collections import OrderedDict

class AniList:
    def __init__(self):
        self.search_query = search_query = '''query ($search: String, $type: MediaType) {
  Page {
    media(search: $search, type: $type) {
      id
      title {
        romaji
        english
        native
      }
      type
      status
      format
      episodes
      chapters
      volumes
      description
      startDate {
          year
          month
          day
      }
      endDate {
          year
          month
          day
      }
      genres
      synonyms
      coverImage {
        large
      }
      isAdult
    }
  }
}'''

        self.id_query = '''query ($id: Int) {
      Page {
        media(id: $id) {
      id
      title {
        romaji
        english
        native
      }
      type
      status
      format
      episodes
      chapters
      volumes
      description
      startDate {
          year
          month
          day
      }
      endDate {
          year
          month
          day
      }
      genres
      synonyms
      coverImage {
        large
      }
      isAdult
        }
      }
    }'''

        self.uri = 'https://graphql.anilist.co'
        self.req = requests.Session()
        
    def morph_to_v1(self, raw):
        raw_results = raw["data"]["Page"]["media"]
        morphed_results = []
        for raw_result in raw_results:
            try:
                morphed = {}
                morphed["id"] = raw_result["id"]
                morphed["title_romaji"] = raw_result["title"]["romaji"]
                morphed["title_english"] = raw_result["title"]["english"]
                morphed["title_japanese"] = raw_result["title"]["native"]
                morphed["type"] = self.map_media_format(raw_result["format"])
                morphed["start_date_fuzzy"] = raw_result["startDate"]
                morphed["start_date"] = f'{morphed["start_date_fuzzy"]["month"]}-{morphed["start_date_fuzzy"]["day"]}-{morphed["start_date_fuzzy"]["year"]}'
                morphed["end_date_fuzzy"] = raw_result["endDate"]
                morphed["end_date"] = f'{morphed["end_date_fuzzy"]["month"]}-{morphed["end_date_fuzzy"]["day"]}-{morphed["end_date_fuzzy"]["year"]}'
                morphed["description"] = raw_result["description"]
                morphed["genres"] = raw_result["genres"]
                morphed["synonyms"] = raw_result["synonyms"]
                morphed["total_episodes"] = raw_result["episodes"]
                morphed["total_chapters"] = raw_result["chapters"]
                morphed["total_volumes"] = raw_result["volumes"]
                morphed["airing_status"] = self.map_media_status(raw_result["status"])
                morphed["publishing_status"] = self.map_media_status(raw_result["status"])
                morphed["img"] = raw_result["coverImage"]['large']
                morphed["adult"] = raw_result["isAdult"]
                morphed_results.append(morphed)
            except Exception as e:
                print(e)
        
        return morphed_results

    def map_media_format(self, media_format):
        mapped_formats = {
            'TV': 'TV',
            'TV_SHORT': 'TV Short',
            'MOVIE': 'Movie',
            'SPECIAL': 'Special',
            'OVA': 'OVA',
            'ONA': 'ONA',
            'MUSIC': 'Music',
            'MANGA': 'Manga',
            'NOVEL': 'Novel',
            'ONE_SHOT': 'One Shot',
            }
        return mapped_formats[media_format]

    def map_media_status(self, media_status):
        mapped_status = {
            'FINISHED': 'Finished',
            'RELEASING': 'Releasing',
            'NOT_YET_RELEASED': 'Not Yet Released',
            'CANCELLED': 'Special'
            }
        return mapped_status[media_status]

    #Anilist's database doesn't like weird symbols when searching it, so you have to escape or replace a bunch of stuff.
    def escape(self, text):
         return "".join(escape_table.get(c,c) for c in text)

    def getSynonyms(self, request):
        synonyms = []
        synonyms.extend(request['synonyms']) if request['synonyms'] else None
        return synonyms

    def getTitles(self, request):
        titles = [] 
        titles.append(request['title_english']) if request['title_english'] else None
        titles.append(request['title_romaji']) if request['title_romaji'] else None
        return titles

    def detailsBySearch(self, searchText, mediaType):
        try:
            search_variables = {
                'search': searchText,
                'type': mediaType
            }
            
            request = self.req.post(self.uri, json={ 'query': self.search_query, 'variables': search_variables})
            self.req.close()

            return self.morph_to_v1(request.json())
                
        except Exception as e:
            traceback.print_exc()
            self.req.close()
            return None

    def detailsById(self, idToFind):
        try:
            id_variables = {
                'id': int(idToFind)
            } 
            
            request = self.req.post(self.uri, json={ 'query': self.id_query, 'variables': id_variables})
            self.req.close()
            return self.morph_to_v1(request.json())[0]
                
        except Exception as e:
            traceback.print_exc()
            self.req.close()
            return None

    #Returns the closest anime (as a Json-like object) it can find using the given searchtext
    def getAnimeDetails(self, searchText):
        try:
            results = self.detailsBySearch(searchText, 'ANIME')
            
            #Of the given list of shows, we try to find the one we think is closest to our search term
            closest_anime = self.getClosestAnime(searchText, results)

            if closest_anime:
                return closest_anime
            else:
                return None
                
        except Exception as e:
            traceback.print_exc()
            self.req.close()
            return None

    #Returns the anime details based on an id
    def getAnimeDetailsById(self, animeID):
        try:
            return self.detailsById(animeID)
        except Exception as e:
            print(e)
            return None

    #Given a list, it finds the closest anime series it can.
    def getClosestAnime(self, searchText, animeList):
        try:
            animeNameList = []
            animeNameListNoSyn = []

            #For each anime series, add all the titles/synonyms to an array and do a fuzzy string search to find the one closest to our search text.
            #We also fill out an array that doesn't contain the synonyms. This is to protect against shows with multiple adaptations and similar synonyms (e.g. Haiyore Nyaruko-San)
            animeList = [x for x in animeList if not x["adult"]]
            if not animeList:
                return None
            for anime in animeList:
                if 'title_english' in anime and anime['title_english']:
                    animeNameList.append(anime['title_english'].lower())
                    animeNameListNoSyn.append(anime['title_english'].lower())

                if 'title_romaji' in anime and anime['title_romaji']:
                    animeNameList.append(anime['title_romaji'].lower())
                    animeNameListNoSyn.append(anime['title_romaji'].lower())

                if 'synonyms' in anime and anime['synonyms']:
                    for synonym in anime['synonyms']:
                         animeNameList.append(synonym.lower())
            try:
                closestNameFromList = difflib.get_close_matches(searchText.lower(), animeNameList, 1, 0.95)[0]
            except:
                closestNameFromList = animeNameList[0]
            if closestNameFromList:
                for anime in animeList: 
                    if anime['title_english'] and anime['title_english'].lower() == closestNameFromList.lower():
                        return anime
                    elif anime['title_romaji'] and anime['title_romaji'].lower() == closestNameFromList.lower():
                        return anime
                    else:
                        for synonym in anime['synonyms']:
                            if (synonym.lower() == closestNameFromList.lower()) and (synonym.lower() not in animeNameListNoSyn):
                                return anime

            return None
        except:
            traceback.print_exc()
            return None

    def getLightNovelDetails(self, searchText):
        return self.getMangaDetails(searchText, True)

    #Returns the closest manga series given a specific search term
    def getMangaDetails(self, searchText, isLN=False):
        try:       
            results = self.detailsBySearch(searchText, 'MANGA')
            
            closestManga = self.getClosestManga(searchText, results, isLN)

            if closestManga:
                return closestManga
            else:
                return None
            
        except Exception as e:
            #traceback.print_exc()
            return None

    #Returns the closest manga series given an id
    def getMangaDetailsById(self, mangaId):
        try:
            return self.detailsById(mangaId)
        except Exception as e:
            return None

    #Used to determine the closest manga to a given search term in a list
    def getListOfCloseManga(self, searchText, mangaList):
        try:
            ratio = 0.90
            returnList = []
            
            for manga in mangaList:
                alreadyExists = False
                for thing in returnList:
                    if int(manga['id']) == int(thing['id']):
                        alreadyExists = True
                        break
                if (alreadyExists):
                    continue
                
                if manga['title_english'] and round(difflib.SequenceMatcher(lambda x: x == "", manga['title_english'].lower(), searchText.lower()).ratio(), 3) >= ratio:
                    returnList.append(manga)
                elif manga['title_romaji'] and round(difflib.SequenceMatcher(lambda x: x == "", manga['title_romaji'].lower(), searchText.lower()).ratio(), 3) >= ratio:
                    returnList.append(manga)
                elif not (manga['synonyms'] is None):
                    for synonym in manga['synonyms']:
                        if round(difflib.SequenceMatcher(lambda x: x == "", synonym.lower(), searchText.lower()).ratio(), 3) >= ratio:
                            returnList.append(manga)
                            break
            return returnList
        except Exception as e:
            traceback.print_exc()
            return None

    #Used to determine the closest manga to a given search term in a list
    def getClosestManga(self, searchText, mangaList, isLN=False):
        try:
            mangaNameList = []
            mangaList = [x for x in mangaList if not x['adult']]
            if not mangaList:
                return None
            if isLN:
                mangaList = [x for x in mangaList if 'novel' in x['type'].lower()]
            else:
                mangaList = [x for x in mangaList if 'novel' not in x['type'].lower()]
            if not mangaList:
                return None
            for manga in mangaList:
                mangaNameList.append(manga['title_english'].lower()) if manga['title_english'] else None
                mangaNameList.append(manga['title_romaji'].lower()) if manga['title_romaji'] else None

                for synonym in manga['synonyms']:
                     mangaNameList.append(synonym.lower())

            try:
                closestNameFromList = difflib.get_close_matches(searchText.lower(), mangaNameList, 1, 0.90)[0]
            except:
                closestNameFromList = mangaNameList[0]
            if closestNameFromList:
                for manga in mangaList:
                    if not ('one shot' in manga['type'].lower()):
                        if manga['title_english'] and (manga['title_english'].lower() == closestNameFromList.lower()):
                            return manga
                        if manga['title_romaji'] and (manga['title_romaji'].lower() == closestNameFromList.lower()):
                            return manga

                for manga in mangaList:                
                    for synonym in manga['synonyms']:
                        if synonym.lower() == closestNameFromList.lower():
                            return manga

            return None
        except Exception as e:
            traceback.print_exc()
            return None


class MALBOT:

    def __init__(self, bot):
        self.bot = bot
        self.anilist = AniList()
        self.bot.anilist = self.anilist
        self.bot.ani_get_options = self.get_option
        
        
    async def get_option(self, args, mobj, search_type):
        try:
            author = mobj.author
            if search_type == 'LN':
                searcher = 'MANGA'
            else:
                searcher = search_type
            results = self.anilist.detailsBySearch(args, searcher)
            if search_type == 'LN':
                results = [x for x in results if 'novel' in x['type'].lower()]
            elif search_type == 'MANGA':
                results = [x for x in results if 'novel' not in x['type'].lower()]
            potentials = results
            
             
            if len(potentials) == 1:
                return potentials[0]['id']
            elif len(potentials) < 1:
                return None
            questions = []
            for cur in potentials:
                for language in ["title_english", "title_romaji", "title_japanese"]:
                    if cur[language]:
                        questions.append((cur[language], cur['id']))
                        break
            order = sorted(questions, key = lambda x : fuzz.ratio(args, questions), reverse=True)[:15]
            cards_ = OrderedDict([(i,v) for i,v in enumerate(order)])
            
            message = "```Which series would you like:\n"
            for anime in cards_.items():

                message += "[{}] {}\n".format(str(anime[0] + 1), anime[1][0])

            message += "\nUse the number to the side of the name as a key to select it!```"

            await self.bot.message(mobj.channel, message)

            msg = await self.bot.client.wait_for_message(timeout=10.0, author=author)

            if not msg:
                await self.bot.error(mobj.channel, "Operation has timed out, please try again.")
                return None
            try:
                key = int(msg.content) - 1
            except:
                await self.bot.error(mobj.channel, "Invalid Key")
                return None
            return cards_[key][1]
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

    @ChatBot.action("[String]")
    async def anime(self, args, mobj):

        """
        Does a AniList search to find requested Anime
        
        If there are multiple options, will ask you which one to choose. You will have 10 seconds to respond.
        
        Will not return any adult series.
        """
        args = " ".join(args)
        
        result = await self.ani_get_options(args, mobj, 'ANIME')
        
        if result:
            anime = self.anilist.getAnimeDetailsById(result)
        else:
            anime = self.anilist.getAnimeDetails(args)
        if not anime:
            await self.error(mobj.channel, "Could not find anything")
            return
        
        
        if not anime:
            await self.error(mobj.channel, "Could not find anything")
            return

        embed = Embed(
            title=anime['title_english'] if anime['title_english'] else anime['title_romaji'] if anime['title_romaji'] else anime['title_japanese'],
            colour=Color(0x7289da),
            url=f"https://anilist.co/anime/{anime['id']}/{anime['title_romaji']}".replace(" ", "%20")
        )
        embed.set_image(url=anime['img'])
        embed.add_field(name="Episode Count", value=str(anime['total_episodes']))
        embed.add_field(name="Type", value=anime['type'])
        embed.add_field(name="Status", value=anime['airing_status'])
        
        embed.add_field(
            name="Dates",
            value=f'{anime["start_date"]} through {anime["end_date"] if anime["end_date"] != "None-None-None" else "present"}' if anime["start_date"] != anime["end_date"] else f'{anime["start_date"]}')
            
        if anime["synonyms"]:
            embed.add_field(
                name="Synonyms",
                value=", ".join(anime["synonyms"]))
        if anime["description"] is None:
            anime["description"] = "Could not pull synopsis"            
        anime["description"] = re.sub(r'\n\s*\n', '\n\n', unescape(
            anime["description"]).replace("<br>", "\n"))
        if len(anime["description"]) > 1000:
            if "\n" in anime["description"][:965]:
                anime["description"] = anime["description"][:anime["description"][:965].rfind(
                    "\n")]
            else:
                anime["description"] = anime["description"][:965]
            anime["description"] += "\nIncomplete synopsis due to length."
            
        embed.add_field(
            name="Synopsis",
            value=anime["description"])
        try:
            await self.embed(mobj.channel, embed)
        except BaseException:
            await self.error(mobj.channel, "Something when trying to format the object. Here is a link to the anime: " + "https://myanimelist.net/anime/{0.id}/{0.title}".format(anime).replace(" ", "%20"))

    @ChatBot.action("[String]")
    async def manga(self, args, mobj):

        """
        Does a AniList search to find requested Manga.
            
        If there are multiple options, will ask you which one to choose. You will have 10 seconds to respond.
            
        Will not return any adult series.
        """
        args = " ".join(args)
        
        result = await self.ani_get_options(args, mobj, 'MANGA')
        if result:
            manga = self.anilist.getMangaDetailsById(result)
        else:
            manga = self.anilist.getMangaDetails(args, True)
        
        if not manga:
            await self.error(mobj.channel, "Could not find anything")
            return

        embed = Embed(
            title=manga['title_english'] if manga['title_english'] else manga['title_romaji'] if manga['title_romaji'] else manga['title_japanese'],
            colour=Color(0x7289da),
            url=f"https://anilist.co/manga/{manga['id']}/{manga['title_romaji']}".replace(" ", "%20")
        )
        # embed.set_author(name=author.display_name, icon_url=avatar)
        embed.set_image(url=manga['img'])
        embed.add_field(
            name="Length",
            value=f'{manga["total_chapters"] if manga["total_chapters"] else 0} Chapters, {manga["total_volumes"] if manga["total_volumes"] else 0} Volumes')
        embed.add_field(name="Type", value=manga["type"])
        embed.add_field(name="Status", value=manga["airing_status"])
        embed.add_field(
            name="Dates",
            value=f'{manga["start_date"]} through {manga["end_date"] if manga["end_date"] != "None-None-None" else "present"}' if manga["start_date"] != manga["end_date"] else f'{manga["start_date"]}')
            
        if manga["synonyms"]:
            embed.add_field(
                name="Synonyms",
                value=", ".join(manga["synonyms"]))
        if manga["description"] is None:
            manga["description"] = "Could not pull synopsis"                
        manga["description"] = re.sub(r'\n\s*\n', '\n\n', unescape(
            manga["description"]).replace("<br>", "\n"))
        if len(manga["description"]) > 1000:
            if "\n" in manga["description"][:965]:
                manga["description"] = manga["description"][:manga["description"][:965].rfind(
                    "\n")]
            else:
                manga["description"] = manga["description"][:965]
            manga["description"] += "\nIncomplete synopsis due to length."

        embed.add_field(
            name="Synopsis",
            value=manga["description"])

        try:
            await self.embed(mobj.channel, embed)
        except BaseException:
            await self.error(mobj.channel, "Something when trying to format the object. Here is a link to the manga: " + "https://myanimelist.net/manga/{0.id}/{0.title}".format(manga).replace(" ", "%20"))

    @ChatBot.action("[String]")
    async def ln(self, args, mobj):
        try:
            """
            Does a AniList search to find requested Light Novel.
            
            If there are multiple options, will ask you which one to choose. You will have 10 seconds to respond.
            
            Will not return any adult series.
            """
            args = " ".join(args)
            result = await self.ani_get_options(args, mobj, 'LN')
            if result:
                manga = self.anilist.getMangaDetailsById(result)
            else:
                manga = self.anilist.getMangaDetails(args)
            
            if not manga:
                await self.error(mobj.channel, "Could not find anything")
                return
            embed = Embed(
                title=manga['title_english'] if manga['title_english'] else manga['title_romaji'] if manga['title_romaji'] else manga['title_japanese'],
                colour=Color(0x7289da),
                url=f"https://anilist.co/manga/{manga['id']}/{manga['title_romaji']}".replace(" ", "%20")
            )
            # embed.set_author(name=author.display_name, icon_url=avatar)
            embed.set_image(url=manga['img'])
            embed.add_field(
                name="Length",
                value=f'{manga["total_chapters"] if manga["total_chapters"] else 0} Chapters, {manga["total_volumes"] if manga["total_volumes"] else 0} Volumes')
            embed.add_field(name="Type", value=manga["type"])
            embed.add_field(name="Status", value=manga["airing_status"])
            embed.add_field(
                name="Dates",
                value=f'{manga["start_date"]} through {manga["end_date"] if manga["end_date"] != "None-None-None" else "present"}' if manga["start_date"] != manga["end_date"] else f'{manga["start_date"]}')
                
            if manga["synonyms"]:
                embed.add_field(
                    name="Synonyms",
                    value=", ".join(manga["synonyms"]))
                
            if manga["description"] is None:
                manga["description"] = "Could not pull synopsis"
            manga["description"] = re.sub(r'\n\s*\n', '\n\n', unescape(
                manga["description"]).replace("<br>", "\n"))
            if len(manga["description"]) > 1000:
                if "\n" in manga["description"][:965]:
                    manga["description"] = manga["description"][:manga["description"][:965].rfind(
                        "\n")]
                else:
                    manga["description"] = manga["description"][:965]
                manga["description"] += "\nIncomplete synopsis due to length."

            embed.add_field(
                name="Synopsis",
                value=manga["description"])

            try:
                await self.embed(mobj.channel, embed)
            except BaseException:
                await self.error(mobj.channel, "Something when trying to format the object. Here is a link to the manga: " + "https://myanimelist.net/manga/{0.id}/{0.title}".format(manga).replace(" ", "%20"))
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)

def setup(bot):
    MALBOT(bot)
