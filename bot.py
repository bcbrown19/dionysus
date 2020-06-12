import discord
import keyring
from pymongo import MongoClient
import logging
import re
import inflect
import random

mc = MongoClient('mongodb://localhost:27017')
db = mc.streamers
sc = db.streamers_collection
mc.close()

REGISTER_MESSAGE_ID = 664824406576594966
BOT_CHANNEL_ID = 656489712944545792
TWITCH_ID = 53366984

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger('discord')
        self.logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(filename='/opt/discord/discord.log', encoding='utf-8', mode='w')
        handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
        self.logger.addHandler(handler)

    async def on_ready(self):
        self.logger.info(f'Logged on as {self.user}')

    async def on_message(self, message):
        if message.channel.id == BOT_CHANNEL_ID and not message.author.bot:
            print(f'Message from {message.author}: {message.content}')

        # register a twitch channel name wit the bot
        if message.content.startswith('$register') and 'private' in message.channel.type:
            ctx = message.channel
            twitch_channel = message.content.split(' ',2)[1]
            
            # connect to mongodb - streamers -> streamers_collection
            mc = MongoClient('mongodb://localhost:27017')
            db = mc.streamers
            sc = db.streamers_collection

            streamer_entry = {
                "name": message.author.name,
                "channel": twitch_channel,
                "discord_id": str(message.author.id)
            }
            
            sc.insert_one(streamer_entry)
            self.logger.info(f'{message.author.name} added to mongodb')
            await ctx.send("Thanks! You are now registered with me as a streamer!")

        # command to perform random dice rolls for D&D specifically
        if message.content.startswith('$roll'):
            if "+" in message.content.strip() or "-" in message.content.strip():
                regex = r'^\$roll\s(?P<num_of_dice>\d+)d(?P<die_type>\d+)(?P<mod>[-|+])(?P<mod_int>\d+)$'
                matches = re.search(regex, message.content.strip())
                rolls = []
                for x in range(int(matches.group('num_of_dice'))):
                    rolls.append(random.randint(1,int(matches.group('die_type'))))
                total = sum(rolls)
                if "+" in matches.group('mod'):
                    total += int(matches.group('mod_int'))
                else:
                    total -= int(matches.group('mod_int'))
                ctx = message.channel
                reply_message = """
```
The dice land on: {0}
Your modifier is: {1}{2}
Your total is: {3}
```
                """.format(rolls, matches.group('mod'), matches.group('mod_int'), total)
                await ctx.send(reply_message)

            else:
                regex = r'^\$roll\s(?P<num_of_dice>\d+)d(?P<die_type>\d+)$'
                matches = re.search(regex, message.content.strip())
                rolls = []
                for x in range(int(matches.group('num_of_dice'))):
                    rolls.append(random.randint(1,int(matches.group('die_type'))))
                total = sum(rolls)
                ctx = message.channel
                reply_message = """
```
The dice land on: {0}
Your total is: {1}
```
                """.format(rolls, total)
                await ctx.send(reply_message)

    async def on_raw_reaction_add(self, payload):
        if payload.message_id == REGISTER_MESSAGE_ID:
            user = self.get_user(payload.user_id)
            ctx = await user.create_dm()
            await ctx.send("Hello! You've requested to register your channel with me."\
                    "In order to register your channel, reply to this DM with the command"\
                    " '$register <channel name>'.\n\nFor example: $register theangryginger")
            self.logger.info(f'{user.name} added a reaction')
        else:
            return

client = MyClient()
client.run(keyring.get_password('discord','token'))
