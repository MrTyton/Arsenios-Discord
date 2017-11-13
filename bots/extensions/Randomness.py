from discord import Embed, Color
from random import randint, choice
from Bot import ChatBot
from os.path import isfile
from pathlib import Path
from google.google import search
import strawpy
import asyncio
import xkcd
import re


class RANDOMBOT():

    def __init__(self, bot):
        self.bot = bot
        self.bot.eightball = self.load_eightball()

    def load_eightball(self):
        """
        Load Magic 8-ball answers
        """
        if isfile(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.8ball')):
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.8ball'), 'r') as fp:
                return list(map(str.strip, fp.readlines()))
        else:
            self.bot.logger("There is no 8ball file, creating.")
            with open(Path(self.bot.DATA_FOLDER, f'{self.bot.name}.8ball'), 'w') as fp:
                fp.write("I have no idea, I'm not psychic.")
            return ["I have no idea, I'm not psychic."]

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
        if not args:
            return await self.error(mobj.channel, "Question is hazy, please try again.")

        return await self.message(mobj.channel, choice(self.eightball))

    @ChatBot.action('[Number]|[Number d Number]')
    async def roll(self, args, mobj):
        """
        1) Make a roll between [1..1000]
        Example: !roll 100
        2) Roll XdY [max 100 dice, max 1000 sides. If you choose too large options then it might not print the result.]
        Example: !roll 3d6
        """
        if not args or len(args) > 1:
            return await self.error(mobj.channel, "Invalid arg count")

        x, = args
        if x == "barrel":
            return await self.message(mobj.channel, "https://www.youtube.com/watch?v=mv5qzMtLE60")
        if 'd' in x:
            dice, sides = x.split("d")
            ans = []
            if not dice.isnumeric() or not sides.isnumeric():
                return await self.error(mobj.channel, "Non-numeric args given.")
            if int(dice) > 100 or int(dice) < 1 or int(
                    sides) > 1000 or int(sides) < 1:
                return await self.message(mobj.channel, "Invalid Argument Range")
            for i in range(int(dice)):
                ans.append(randint(1, int(sides)))
            summation = sum(ans)
            res = "+".join(["".join(self.emojis[x] for x in str(y).zfill(len(str(y)))) for y in ans]) + \
                "=" + "".join([self.emojis[x] for x in str(summation).zfill(len(str(summation)))])
        else:
            if not x.isnumeric():
                return await self.error(mobj.channel, "Non-numeric arg given")

            num = int(x)  # bad
            if num < 1 or num > 1000:
                return await self.error(mobj.channel, "Invalid range given")

            res = [self.emojis[x] for x in str(randint(1, num)).zfill(len(x))]
        return await self.message(mobj.channel, "".join(res))

    @ChatBot.action('[String]')
    async def spam(self, args, mobj):
        """
        Spam a channel with dumb things
        Example: !spam :ok_hand:
        """
        if not args:
            return await self.message(mobj.channel, "Invalid spam input")
        argl = len(f"{' '.join(args)}")
        max_length = 2000 // argl
        if max_length < 5:
            return await self.message(mobj.channel, "Invalid spam input")
        y = args * randint(5, min(max_length, 20))
        return await self.message(mobj.channel, f"{' '.join(y)}")

    @ChatBot.action('[String]')
    async def xkcd(self, args, mobj):
        """
        Returns the most likely xkcd to be referenced by the keywords
        """

        xkcd_urls = search(f"site:xkcd.com -forums -wiki -blog {' '.join(args)}", 3)
        match = False
        for i, cur in enumerate(xkcd_urls):
            id = re.match(r"https://[\.m]*xkcd.com/(\d*)/", cur.link)
            if id:
                match = True
                break
        if not match:
            return await self.error(mobj.channel, "Nothing Found")

        comic = xkcd.getComic(int(id.group(1)))

        if comic == -1:
            return await self.error(mobj.channel, "Nothing Found")

        embed = Embed(
            title=comic.getTitle(),
            url=f"https://xkcd.com/{id.group(1)}",
            colour=Color(0x7289da)
        )
        embed.set_image(url=comic.getImageLink())
        embed.add_field(name="Alt-Text", value=comic.getAltText())
        embed.add_field(name="Explanation", value=f"[Link]({comic.getExplanation()})")
        return await self.embed(mobj.channel, embed)

    @ChatBot.action('[Title] = [Option 1] | [Option 2]...')
    async def poll(self, args, mobj):
        """
        Create a strawpoll.
        Format is Title = Options | Separated | By | These things
        Example: !poll Favorite color = Blue | Red | Green
        """
        args = " ".join(args)
        loop = asyncio.get_event_loop()
        try:
            options = [op.strip() for op in args.split('|')]
            if '=' in options[0]:
                title, options[0] = options[0].split('=')
                options[0] = options[0].strip()
            else:
                title = f'Poll by {mobj.author.name}'
        except BaseException:
            return await self.error(mobj.channel, 'Invalid Syntax.')

        poll = await loop.run_in_executor(None, strawpy.create_poll, title.strip(), options)
        await self.message(mobj.channel, f"{poll.url}")


def setup(bot):
    RANDOMBOT(bot)
