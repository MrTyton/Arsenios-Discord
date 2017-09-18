
from Bot import ChatBot
from discord import Embed, Color
from mtgsdk import Card


class CARDBOT:

    def __init__(self, bot):
        self.bot = bot
        self.bot.get_card = self.get_card  # there has to be a better way to do this
        self.bot.magic_emojis = {}
        self.bot.card_get_image = self.card_get_image

    async def get_card(self, args, mobj):
        author = mobj.author
        try:
            cards = Card.where(name=" ".join(args)).iter()
        except BaseException:
            await self.bot.message(mobj.channel, "Something broke when requesting cards.")
            return None

        cards_ = dict()
        entered = []
        a = 0
        for cur in cards:
            if cur.name not in entered:
                cards_[a] = cur
                a += 1
                entered.append(cur.name)
                if len(entered) >= 15:
                    break
        if len(cards_) == 0:
            await self.bot.message(mobj.channel, "No cards found.")
            return None
        if len(cards_) > 1:
            message = "```What card would you like:\n"
            for anime in cards_.items():

                message += "[{}] {}\n".format(str(anime[0] + 1), anime[1].name)

            message += "\nUse the number to the side of the name as a key to select it!```"

            await self.bot.message(mobj.channel, message)

            msg = await self.bot.client.wait_for_message(timeout=10.0, author=author)

            if not msg:
                return None

            key = int(msg.content) - 1
        else:
            key = 0

        try:
            return cards_[key]
        except (ValueError, KeyError):
            await self.bot.message(mobj.channel, "Invalid key.")
            return None

    @ChatBot.action('[Card Name]')
    async def card(self, args, mobj):

        """
        Does a search for requested magic card.
        If there are multiple cards with similar name, will prompt to select one.
        Displays only the picture of the card. For full information use !cardfull
        """

        card = await self.get_card(args, mobj)
        if not card:
            return

        embd = Embed(
            title=card.name,
            colour=Color(0x7289da),
            url=f"http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={card.multiverse_id}"
        )
        last_set = card.printings[-1]
        latest_picture = self.card_get_image(card, last_set)
        embd.set_image(url=latest_picture.image_url)

        return await self.embed(mobj.channel, embd)

    def card_get_image(self, card, set):
        iterator = Card.where(name=card.name, set=set).iter()
        for i in iterator:
            return i

    @ChatBot.action('[Card Name]')
    async def cardfull(self, args, mobj):

        """
        Does a search for requested magic card.
        If there are multiple cards with similar name, will prompt to select one.
        Displays all the information about the card. For only the card image, use !card
        """
        card = await self.get_card(args, mobj)
        if not card:
            return

        if not len(self.magic_emojis):
            for cur in self.client.get_all_emojis():
                self.magic_emojis[cur.name] = cur

        mana_dict = {
            "{B}": self.magic_emojis['BlackMana'],
            "{U}": self.magic_emojis['BlueMana'],
            "{W}": self.magic_emojis['WhiteMana'],
            "{R}": self.magic_emojis['RedMana'],
            "{G}": self.magic_emojis['GreenMana'],
            "{X}": self.magic_emojis['XMana'],
            "{C}": self.magic_emojis["CMana"],
            "{U/P}": self.magic_emojis['PhyBlue'],
            "{B/P}": self.magic_emojis['PhyBlack'],
            "{G/P}": self.magic_emojis['PhyGreen'],
            "{W/P}": self.magic_emojis['PhyWhite'],
            "{R/P}": self.magic_emojis['PhyRed'],
            "{0}": self.magic_emojis["0Mana"],
            "{1}": self.magic_emojis["1Mana"],
            "{2}": self.magic_emojis["2Mana"],
            "{3}": self.magic_emojis["3Mana"],
            "{4}": self.magic_emojis["4Mana"],
            "{5}": self.magic_emojis["5Mana"],
            "{6}": self.magic_emojis["6Mana"],
            "{7}": self.magic_emojis["7Mana"],
            "{8}": self.magic_emojis["8Mana"],
            "{9}": self.magic_emojis["9Mana"],
            "{10}": self.magic_emojis["10Mana"],
            "{11}": self.magic_emojis["11Mana"],
            "{12}": self.magic_emojis["12Mana"],
            "{13}": self.magic_emojis["13Mana"],
            "{15}": self.magic_emojis["15Mana"],
            "{T}": self.magic_emojis['Tap'],
        }

        def replace_symbols(input):
            for cur in mana_dict:
                if cur in input:
                    input = input.replace(cur, str(mana_dict[cur]))
            return input

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
            mana_costs = replace_symbols(card.mana_cost)
            embd.add_field(name="Mana Cost", value=mana_costs)
            embd.add_field(name="CMC", value=card.cmc)
        last_set = card.printings[-1]
        embd.add_field(name="Last Printing", value=last_set)
        if len(card.printings) > 1:
            embd.add_field(
                name="Other Printings",
                value=f"{', '.join([x for x in card.printings if x != last_set])}")

        legalities = {x["format"]: f'{x["format"]}: {x["legality"]}' for x in card.legalities if
                      x['legality'] == 'Banned' or x['legality'] == 'Restricted'}
        for format in ["Standard", "Modern", "Legacy", "Vintage"]:
            if format in [x["format"] for x in card.legalities]:
                legalities[format] = [
                    f'{q["format"]}: {q["legality"]}' for q in card.legalities if q["format"] == format][0]
        embd.add_field(name="Legality", value='\n'.join(legalities.values()))
        embd.add_field(name="Type", value=card.type)
        if card.supertypes:
            embd.add_field(
                name="Supertypes",
                value=f"{', '.join(card.supertypes)}")
        if card.subtypes:
            embd.add_field(
                name="Subtypes",
                value=f"{', '.join(card.subtypes)}")
        if 'creature' in card.type:
            embd.add_field(
                name="Power/Toughness",
                value=f"{card.power}/{card.toughness}")
        if 'planeswalker' in card.type:
            embd.add_field(name="Loyalty", value=card.loyalty)
        if card.text:
            text = replace_symbols(card.text)
            embd.add_field(name="Card Text", value=text)
        latest_picture = self.card_get_image(card, last_set)
        embd.set_image(url=latest_picture.image_url)
        try:
            await self.embed(mobj.channel, embd)
        except BaseException:
            await self.message(mobj.channel, "Something went wrong when getting all of the information. Here's the image instead.")
            embd = Embed(
                title=card.name,
                colour=Color(0x7289da),
                url=f"http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={card.multiverse_id}"
            )
            last_set = card.printings[-1]
            latest_picture = self.card_get_image(card, last_set)
            embd.set_image(url=latest_picture.image_url)

            return await self.embed(mobj.channel, embd)


def setup(bot):
    CARDBOT(bot)
