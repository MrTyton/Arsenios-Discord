
from Bot import ChatBot
from discord import Embed, Color
from mtgsdk import Card


class CARDBOT:

    def __init__(self, bot):
        self.bot = bot
        self.bot.get_card = self.get_card  # there has to be a better way to do this
        self.bot.card_get_image = self.card_get_image
        self.bot.card_replace_symbols = self.replace_symbols
        self.bot.magic_dict = {}
        self.bot.card_get_color = self.card_get_color

    def card_get_color(self, card):
        if card.colors:
            if len(card.colors) > 1:
                colors = "Gold"
            else:
                colors = card.colors[0]
        else:
            colors = "Grey"
        color_dict = {"Red": Color.red(),
                      "Blue": Color.blue(),
                      "Green": Color.green(),
                      "Black": Color(0x000000),
                      "White": Color(0xffffff),
                      "Gold": Color.gold(),
                      "Grey": Color.light_grey()}
        return color_dict[colors]

    async def get_card(self, args, mobj):
        author = mobj.author
        try:
            cards = Card.where(name=" ".join(args)).iter()
        except BaseException:
            await self.bot.error(mobj.channel, "Something broke when requesting cards.")
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
            await self.bot.error(mobj.channel, "No cards found.")
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
            await self.bot.error(mobj.channel, "Invalid key.")
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
            colour=self.card_get_color(card),
            url=f"http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={card.multiverse_id}"
        )
        last_set = card.printings[-1]
        latest_picture = self.card_get_image(card, last_set, card.printings)
        if latest_picture:
            embd.set_image(url=latest_picture.image_url)
            return await self.embed(mobj.channel, embd)
        else:
            self.error(
                mobj.channel,
                "There is no image for this card, unsure why.")

    def card_get_image(self, card, set, all_sets):
        iterator = Card.where(name=card.name, set=set).iter()
        for i in iterator:
            if i.name == card.name and i.image_url:
                return i
        all_sets.reverse()
        for cur_printing in all_sets[1:]:
            iterator = Card.where(card=card.name, set=cur_printing).iter()
            for i in iterator:
                if i.name == card.name and i.image_url:
                    return i

    def replace_symbols(self, input, magic_dict):
        for cur in magic_dict:
            if cur in input:
                input = input.replace(cur, str(magic_dict[cur]))
        return input

    @ChatBot.action('[Card Name]')
    async def cardfull(self, args, mobj):

        """
        Does a search for requested magic card.
        If there are multiple cards with similar name, will prompt to select one.
        Displays all the information about the card. For only the card image, use !card
        """
        try:
            card = await self.get_card(args, mobj)
            if not card:
                return
            if mobj.server.id not in self.magic_dict:
                magic_emojis = {}
                for cur in mobj.server.emojis:
                    magic_emojis[cur.name] = cur
                try:
                    mana_dict = {
                        "{B}": magic_emojis['BlackMana'],
                        "{U}": magic_emojis['BlueMana'],
                        "{W}": magic_emojis['WhiteMana'],
                        "{R}": magic_emojis['RedMana'],
                        "{G}": magic_emojis['GreenMana'],
                        "{X}": magic_emojis['XMana'],
                        "{C}": magic_emojis["CMana"],
                        "{U/P}": magic_emojis['PhyBlue'],
                        "{B/P}": magic_emojis['PhyBlack'],
                        "{G/P}": magic_emojis['PhyGreen'],
                        "{W/P}": magic_emojis['PhyWhite'],
                        "{R/P}": magic_emojis['PhyRed'],
                        "{0}": magic_emojis["0Mana"],
                        "{1}": magic_emojis["1Mana"],
                        "{2}": magic_emojis["2Mana"],
                        "{3}": magic_emojis["3Mana"],
                        "{4}": magic_emojis["4Mana"],
                        "{5}": magic_emojis["5Mana"],
                        "{6}": magic_emojis["6Mana"],
                        "{7}": magic_emojis["7Mana"],
                        "{8}": magic_emojis["8Mana"],
                        "{9}": magic_emojis["9Mana"],
                        "{10}": magic_emojis["10Mana"],
                        "{11}": magic_emojis["11Mana"],
                        "{12}": magic_emojis["12Mana"],
                        "{13}": magic_emojis["13Mana"],
                        "{15}": magic_emojis["15Mana"],
                        "{T}": magic_emojis['Tap'],
                    }
                    self.magic_dict[mobj.server.id] = mana_dict
                except BaseException:
                    self.magic_dict[mobj.server.id] = {}

            embd = Embed(
                title=card.name,
                colour=self.card_get_color(card),
                url=f"http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={card.multiverse_id}"
            )
            if card.colors:
                embd.add_field(name="Color", value=f'{", ".join(card.colors)}')
            else:
                embd.add_field(name="Color", value=f'Colorless')
            if card.mana_cost:
                mana_costs = self.card_replace_symbols(
                    card.mana_cost, self.magic_dict[mobj.server.id])
                embd.add_field(name="Mana Cost", value=mana_costs)
                embd.add_field(name="CMC", value=card.cmc)

            last_set = card.printings[-1]
            embd.add_field(name="Last Printing", value=last_set)
            if len(card.printings) > 1:
                embd.add_field(
                    name="Other Printings",
                    value=f"{', '.join([x for x in card.printings if x != last_set])}")
            if card.legalities:
                legalities = {x["format"]: f'{x["format"]}: {x["legality"]}' for x in card.legalities if
                              x['legality'] == 'Banned' or x['legality'] == 'Restricted'}
                for format in ["Standard", "Modern", "Legacy", "Vintage"]:
                    if format in [x["format"] for x in card.legalities]:
                        legalities[format] = [
                            f'{q["format"]}: {q["legality"]}' for q in card.legalities if q["format"] == format][0]
                embd.add_field(
                    name="Legality", value='\n'.join(
                        legalities.values()))
            embd.add_field(name="Type", value=card.type)
            if card.supertypes:
                embd.add_field(
                    name="Supertypes",
                    value=f"{', '.join(card.supertypes)}")
            if card.subtypes:
                embd.add_field(
                    name="Subtypes",
                    value=f"{', '.join(card.subtypes)}")
            if 'Creature' in card.type:
                card.power = card.power.replace("*", "\*")
                card.toughness = card.toughness.replace("*", "\*")
                embd.add_field(
                    name="Power/Toughness",
                    value=f"{card.power}/{card.toughness}")
            if 'Planeswalker' in card.type:
                embd.add_field(name="Loyalty", value=card.loyalty)
            if card.text:
                text = self.card_replace_symbols(
                    card.text, self.magic_dict[mobj.server.id])
                embd.add_field(name="Card Text", value=text)
            latest_picture = self.card_get_image(
                card, last_set, card.printings)
            embd.set_image(url=latest_picture.image_url)
            try:
                await self.embed(mobj.channel, embd)
            except BaseException as e:
                await self.error(mobj.channel, "Something went wrong when getting all of the information. Here's the image instead.")
                embd = Embed(
                    title=card.name,
                    colour=self.card_get_color(card),
                    url=f"http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={card.multiverse_id}"
                )
                last_set = card.printings[-1]
                latest_picture = self.card_get_image(
                    card, last_set, card.printings)
                embd.set_image(url=latest_picture.image_url)

                return await self.embed(mobj.channel, embd)
        except BaseException:
            await self.error(mobj.channel, "Something went wrong when getting the card, unsure what.")


def setup(bot):
    CARDBOT(bot)
