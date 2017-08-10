
from Bot import ChatBot, Bot
from discord import Embed, Color
from mtgsdk import Card

class CARDBOT:

    def __init__(self, bot):
        self.bot = bot
        self.bot.get_card = self.get_card #there has to be a better way to do this
    
    
    async def get_card(self, args, mobj):
        author = mobj.author
        try:
            cards = Card.where(name=" ".join(args)).all()
        except:
            await self.message(mobj.channel, "Something broke when requesting cards.")
            return None
        
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
            await self.message(mobj.channel, "No cards found.")
            return None
        if len(cards_) > 1:
            message = "```What card would you like:\n"
            for anime in cards_.items():
          
                message += "[{}] {}\n".format(str(anime[0]+1), anime[1].name)
            
            message += "\nUse the number to the side of the name as a key to select it!```"

            
            await self.message(mobj.channel, message)

            msg = await self.client.wait_for_message(timeout=10.0, author=author)
            
            if not msg: return None
            
            key = int(msg.content)-1
        else:
            key = 0
            
        try:
            return cards_[key]
        except (ValueError, KeyError):
            await self.message(mobj.channel, "Invalid key.")
            return None
        
    @ChatBot.action('[Card Name]')
    async def card(self, args, mobj):
    
        """
        Does a search for requested magic card.
        If there are multiple cards with similar name, will prompt to select one.
        Displays only the picture of the card. For full information use !cardfull
        """
        
        card = await self.get_card(args, mobj)
        if not card: return
        
        embd = Embed(
            title=card.name,
            colour=Color(0x7289da),
            url=f"http://gatherer.wizards.com/Pages/Card/Details.aspx?multiverseid={card.multiverse_id}"
        )
        last_set = card.printings[-1]
        latest_picture = Card.where(name=card.name, set=last_set).all()[0]
        embd.set_image(url=latest_picture.image_url)
        
        return await self.embed(mobj.channel, embd)

        
    @ChatBot.action('[Card Name]')
    async def cardfull(self, args, mobj):
    
        """
        Does a search for requested magic card.
        If there are multiple cards with similar name, will prompt to select one.
        Displays all the information about the card. For only the card image, use !card
        """
        card = await self.get_card(args, mobj)
        if not card: return
        
        if not len(self.emojis):
            for cur in self.client.get_all_emojis():
                self.emojis[cur.name] = cur
            
        mana_dict = {"{B}":self.emojis['BlackMana'], "{U}":self.emojis['BlueMana'], "{W}":self.emojis['WhiteMana'], "{R}":self.emojis['RedMana'], "{G}":self.emojis['GreenMana'], "{X}":self.emojis['XMana'], "{U/P}":self.emojis['PhyBlue'],"{B/P}":self.emojis['PhyBlack'],"{G/P}":self.emojis['PhyGreen'],"{W/P}":self.emojis['PhyWhite'],"{R/P}":self.emojis['PhyRed'],
                    "{1}":self.emojis["1Mana"],"{2}":self.emojis["2Mana"],"{3}":self.emojis["3Mana"],"{4}":self.emojis["4Mana"],"{5}":self.emojis["5Mana"],"{6}":self.emojis["6Mana"],"{7}":self.emojis["7Mana"],"{8}":self.emojis["8Mana"],"{9}":self.emojis["9Mana"],"{10}":self.emojis["10Mana"],"{15}":self.emojis["15Mana"],"{C}":self.emojis["CMana"],"{0}":self.emojis["0Mana"],"{12}":self.emojis["12Mana"],"{13}":self.emojis["13Mana"],"{11}":self.emojis["11Mana"],
                    "{T}":self.emojis['Tap'],
        
        
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
            #mana_costs = card.mana_cost.replace("{", "").replace("}", " ").strip().split(" ")
            #mana_costs = " ".join([str(mana_dict[cur]) if cur in mana_dict else cur for cur in mana_costs])
        
            embd.add_field(name="Mana Cost", value=mana_costs)
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
            embd.add_field(name="Supertypes", value=f"{', '.join(card.supertypes)}")
        if card.subtypes:
            embd.add_field(name="Subtypes", value=f"{', '.join(card.subtypes)}")
        if 'creature' in card.type:
            embd.add_field(name="Power/Toughness", value=f"{card.power}/{card.toughness}")
        if 'planeswalker' in card.type:
            embd.add_field(name="Loyalty", value=card.loyalty)
        if card.text:
            text = replace_symbols(card.text)
            embd.add_field(name="Card Text", value=text)
        latest_picture = Card.where(name=card.name, set=last_set).all()[0]
        embd.set_image(url=latest_picture.image_url)
        
        return await self.embed(mobj.channel, embd)
        
def setup(bot):
    CARDBOT(bot)