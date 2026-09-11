import discord
from discord import FFmpegPCMAudio
import requests
import hashlib
import random
import string
import os
from dotenv import load_dotenv

play_queue = []


current_title = ""
current_artist = ""

def use_queue(voice):
    global current_title
    global current_artist
    if len(play_queue) > 0:
        next_queue = play_queue.pop()
        next_track = next_queue["id"]
        current_title = next_queue["title"]
        current_artist = next_queue["artist"]
        url = build_stream_url(next_track)         
        source = discord.FFmpegPCMAudio(url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
        voice.play(source, after=lambda e:use_queue(voice))
    else: return

def generate_token(password):
    salt = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
    token = hashlib.md5((password + salt).encode('utf-8')).hexdigest()
    return token, salt

def search_navidrome(query):
    url = os.getenv("NAVIDROME_URL")+"/rest/search2"

    token, salt = generate_token(os.getenv("NAVIDROME_PASSWORD"))
        
    params = {
        "query": query,
        "u": "CringelBot",
        "t": token,
        "s": salt,
        "v": "1.16.1",
        "c": "Cringel Bot",
        "f": "json",
    }
    r = requests.get(url, params=params)
    #print("STATUS:", r.status_code)
    data = r.json()
    #print("JSON RESPONSE:",data)
    try:
        return data["subsonic-response"]["searchResult2"]
    except KeyError:
        return []

def build_stream_url(track_id):
    token, salt = generate_token(os.getenv("NAVIDROME_PASSWORD"))

    return (
        f"{os.getenv('NAVIDROME_URL')}/rest/stream"
        f"?id={track_id}"
        f"&u=CringelBot"
        f"&t={token}"
        f"&s={salt}"
        f"&v=1.16.1"
        f"&c=CringelBot"
    )

#search_navidrome("Elton John")

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.content.startswith("!join"):
            if message.author.voice:
                channel = message.author.voice.channel
                await channel.connect()
                await message.channel.send("Joined the voice channel.")
            else:
                await message.channel.send("You must be in a voice channel.")
                return
        if message.content == "!leave":
            if message.guild.voice_client:
                await message.guild.voice_client.disconnect()
                await message.channel.send("Left the voice channel.")
        if message.content.startswith("!play "):
            voice = message.guild.voice_client
            query = message.content.split(" ", 1)[1]

            if not voice:
                if message.author.voice:
                    channel = message.author.voice.channel
                    await channel.connect()
                    await message.channel.send("Joined the voice channel.")
                    voice = message.guild.voice_client
                else:
                    await message.channel.send("You must be in a voice channel.")
                    return
            
            results = search_navidrome(query)
            songs = results.get("song", [])

            if not songs:
                await message.channel.send("No songs found.")
                return

            track = songs[0]
            track_id = track["id"]
            if not voice.is_playing() and not voice.is_paused():
                global current_title
                global current_artist
                url = build_stream_url(track_id)       
                source = discord.FFmpegPCMAudio(url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
                voice.play(source, after=lambda e:use_queue(voice))
                current_title = track['title']
                current_artist = track['artist']
                await message.channel.send(f"Playing: {track['title']} by {track['artist']}")
            else:
                play_queue.insert(0, {"id": track_id, "title": track['title'], "artist": track['artist']})
                await message.channel.send(f"Added: {track['title']} by {track['artist']} to queue. Position: {len(play_queue)}")

        if message.content.startswith("!search "):
            query = message.content.split(" ", 1)[1]
            results = search_navidrome(query)
            reply = ""
            artists = [a["name"] for a in results.get("artist", [])]
            albums = [a["name"] for a in results.get("album", [])]
            songs = [s["title"] for s in results.get("song", [])]
            if len(artists) > 0:
                reply += "\n**Artists: **\n"
                for artist in artists:
                    reply += f" - {artist}\n"
            if len(albums) > 0:
                reply += "\n**Albums: **\n"
                for album in albums:
                    reply += f" - {album}\n"
            if len(songs) > 0:
                reply += "\n**Songs: **\n"
                for song in songs[:10]:
                    reply += f" - {song}\n"
            await message.channel.send(reply)

        if message.content.startswith("!skip"):
            await message.channel.send(f"Skipping track.")
            voice = message.guild.voice_client
            voice.stop()

        if message.content.startswith("!stop"):
            await message.channel.send(f"Stopped all songs.")
            play_queue.clear()
            voice = message.guild.voice_client
            voice.stop()

        if message.content.startswith("!pause"):
            await message.channel.send(f"Paused.")
            voice = message.guild.voice_client
            voice.pause()

        if message.content.startswith("!resume"):
            await message.channel.send(f"Resuming.")
            voice = message.guild.voice_client
            voice.resume()

        if message.content.startswith("!playing"):
            await message.channel.send(f"**Currently playing**: {current_title} by {current_artist}.")

        if message.content.startswith("!queue"):
            reply = ""
            reply += f"**Currently playing: ** {current_title} by {current_artist}.\n"
            for i, track in enumerate(reversed(play_queue)):
                reply += f"**{i+1}: ** {track['title']} by {track['artist']}.\n"
            await message.channel.send(reply)


        

        

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.getenv("DISCORD_BOT_TOKEN"))