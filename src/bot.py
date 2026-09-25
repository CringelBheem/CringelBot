import discord
from discord_control.commands import *
import  os
from dotenv import load_dotenv

load_dotenv()

user_commands = {
    "!join": join,
    "!leave": leave,
    "!play": play,
    "!search": search,
    "!skip": skip,
    "!stop": stop,
    "!pause": pause,
    "!resume": resume,
    "!playing": playing,
    "!queue": queue,
    "!parrot": parrot,
    "!playalbum": play_album,
    "!silent": silent,
    "!playrandomalbum": play_random_album,
    "!playrandom": play_random,
    "!remove": remove_item,
    "!clearqueue": clear_queue,
    "!shufflequeue": shuffle_queue,
    "!autoplay": autoplay
}


class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return
        
        if not message.content:
            return
        
        command = message.content.split()[0]
        if command in user_commands:
            await user_commands[command](message)

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.getenv("DISCORD_BOT_TOKEN"))

"""
!lyrics
!albuminfo
!artistinfo
!autoplay
!help
"""