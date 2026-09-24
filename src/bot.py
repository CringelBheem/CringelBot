import discord
from discord_control.commands import *
import  os
from dotenv import load_dotenv

load_dotenv()

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.content.startswith("!join"):
            await join(message)

        if message.content == "!leave":
            await leave(message)
            
        if message.content.startswith("!play "):
            await play(message)
                
        if message.content.startswith("!search "):
            await search(message)

        if message.content.startswith("!skip"):
            await skip(message)
           
        if message.content.startswith("!stop"):
            await stop(message)

        if message.content.startswith("!pause"):
            await pause(message)

        if message.content.startswith("!resume"):
            await resume(message)

        if message.content.startswith("!playing"):
            await playing(message)
            
        if message.content.startswith("!queue"):
            await queue(message)
            
        if message.content.startswith("!parrot "):
            await parrot(message)

        if message.content.startswith("!playalbum "):
            await play_album(message)

        if message.content == ("!silent"):
            await silent(message)

        if message.content == ("!playalbum"):
            await play_random_album(message)

        if message.content.startswith("!playrandom"):
            await play_random(message)

        if message.content.startswith("!remove "):
            await remove_item(message)

        if message.content == "!clearqueue":
            await clear_queue(message)

        if message.content == "!shufflequeue":
            await shuffle_queue(message)

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.getenv("DISCORD_BOT_TOKEN"))

"""
!shufflequeue
!lyrics
!albuminfo
!artistinfo
!autoplay
!help
"""