import discord
from discord import FFmpegPCMAudio
import requests
import hashlib
import random
import string
import os
from dotenv import load_dotenv

load_dotenv()

queues = {}
now_playing = {}
silent = {}

def use_queue(voice, guild_id):
    if len(queues[guild_id]) > 0:
        next_queue = queues[guild_id].pop()
        next_track = next_queue["id"]
        now_playing[guild_id]["title"] = next_queue["title"]
        now_playing[guild_id]["artist"] = next_queue["artist"]
        url = build_stream_url(next_track)         
        source = discord.FFmpegPCMAudio(url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
        voice.play(source, after=lambda e:use_queue(voice, guild_id))
    else:
        if guild_id in now_playing:
            now_playing[guild_id]["title"] = ""
            now_playing[guild_id]["artist"]= ""
        return

def initialise_globals(message):
    guild_id = message.guild.id
    if guild_id not in queues:
        queues[guild_id] = []
    if guild_id not in now_playing:
        now_playing[guild_id] = {
            "title": "",
            "artist": ""
            }
    if guild_id not in silent:
        silent[guild_id] = 0
    return guild_id

def generate_token(password):
    salt = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
    token = hashlib.md5((password + salt).encode('utf-8')).hexdigest()
    return token, salt

def search_navidrome(query, s_type):
    url = os.getenv("NAVIDROME_URL")+f"/rest/{s_type}"

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
        return {
            "artist": [],
            "album": [],
            "song": []
        }

def search_album(query):
    url = os.getenv("NAVIDROME_URL")+f"/rest/getAlbum"

    token, salt = generate_token(os.getenv("NAVIDROME_PASSWORD"))
     
    results = search_navidrome(query, "search2")
    albums = results.get("album", [])
    if not albums:
        return []
    id = albums[0]["id"]


    params = {
            "id": id,
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
        return data["subsonic-response"]["album"]["song"]
    except KeyError:
        return []

def search_random(size):
    url = os.getenv("NAVIDROME_URL")+f"/rest/getRandomSongs"

    token, salt = generate_token(os.getenv("NAVIDROME_PASSWORD"))

    params = {
            "size": size if size else 1,
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
        return data["subsonic-response"]["randomSongs"]["song"]
    except KeyError:
        return []

#print(search_album("Madman"))

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

#search_navidrome("Elton John", "search2")

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        if message.content.startswith("!join"):
            guild_id = initialise_globals(message)
            if message.author.voice:
                channel = message.author.voice.channel
                await channel.connect()
                if silent[guild_id] == 0:
                    await message.channel.send("Joined the voice channel.")
            else:
                if silent[guild_id] == 0:
                    await message.channel.send("You must be in a voice channel.")
            if silent[guild_id] == 1:
                await message.delete()

        if message.content == "!leave":
            guild_id = initialise_globals(message)
            if guild_id in now_playing:
                now_playing[guild_id]["title"] = ""
                now_playing[guild_id]["artist"]= ""
            if guild_id in queues:
                queues[guild_id].clear()
            if message.guild.voice_client:
                await message.guild.voice_client.disconnect()
                if silent[guild_id] == 0:
                    await message.channel.send("Left the voice channel.")
            if silent[guild_id] == 1:
                await message.delete()
        if message.content.startswith("!play "):
            guild_id = initialise_globals(message)
            voice = message.guild.voice_client
            query = message.content.split(" ", 1)[1]

            if not voice:
                if message.author.voice:
                    channel = message.author.voice.channel
                    await channel.connect()
                    if silent[guild_id] == 0:
                        await message.channel.send("Joined the voice channel.")
                    voice = message.guild.voice_client
                else:
                    if silent[guild_id] == 0:
                        await message.channel.send("You must be in a voice channel.")
                    return
            
            results = search_navidrome(query, "search2")
            songs = results.get("song", [])

            if not songs:
                if silent[guild_id] == 0:
                    await message.channel.send("No songs found.")
                elif silent[guild_id] == 1:
                    await message.delete()
                return

            track = songs[0]
            track_id = track["id"]
            if not voice.is_playing() and not voice.is_paused():
                url = build_stream_url(track_id)       
                source = discord.FFmpegPCMAudio(url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
                voice.play(source, after=lambda e:use_queue(voice, guild_id))
                now_playing[guild_id]["title"] = track['title']
                now_playing[guild_id]["artist"] = track['artist']
                if silent[guild_id] == 0:
                    await message.channel.send(f"Playing: {track['title']} by {track['artist']}")
            else:
                queues[guild_id].insert(0, {"id": track_id, "title": track['title'], "artist": track['artist']})
                if silent[guild_id] == 0:
                    await message.channel.send(f"Added: {track['title']} by {track['artist']} to queue. Position: {len(queues[guild_id])}")
            if silent[guild_id] == 1:
                await message.delete()
                
        if message.content.startswith("!search "):
            query = message.content.split(" ", 1)[1]
            results = search_navidrome(query, "search2")
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
            guild_id = initialise_globals(message)
            if silent[guild_id] == 0:
                await message.channel.send(f"Skipping track.")
            voice = message.guild.voice_client
            voice.stop()
            if silent[guild_id] == 1:
                await message.delete()

        if message.content.startswith("!stop"):
            guild_id = initialise_globals(message)
            if silent[guild_id] == 0:
                await message.channel.send(f"Stopped all songs.")
            queues[guild_id].clear()
            voice = message.guild.voice_client
            voice.stop()
            if silent[guild_id] == 1:
                await message.delete()

        if message.content.startswith("!pause"):
            guild_id = initialise_globals(message)
            if silent[guild_id] == 0:
                await message.channel.send(f"Paused.")
            voice = message.guild.voice_client
            voice.pause()
            if silent[guild_id] == 1:
                await message.delete()

        if message.content.startswith("!resume"):
            guild_id = initialise_globals(message)
            if silent[guild_id] == 0:
                await message.channel.send(f"Resuming.")
            voice = message.guild.voice_client
            voice.resume()
            if silent[guild_id] == 1:
                await message.delete()

        if message.content.startswith("!playing"):
            guild_id = message.guild.id
            if (guild_id not in now_playing or now_playing[guild_id]["title"] == ""):
                await message.channel.send("Nothing is currently playing.")
                return
            await message.channel.send(f"**Currently playing**: {now_playing[guild_id]['title']} by {now_playing[guild_id]['artist']}.")

        if message.content.startswith("!queue"):
            guild_id = message.guild.id
            if guild_id not in now_playing:
                await message.channel.send("Nothing is currently playing.")
                return
            if now_playing[guild_id]["title"] == "":
                await message.channel.send("Nothing is currently playing.")
                return
            reply = f"**Currently playing: ** {now_playing[guild_id]['title']} by {now_playing[guild_id]['artist']}.\n"
            for i, track in enumerate(reversed(queues[guild_id])):
                reply += f"**{i+1}: ** {track['title']} by {track['artist']}.\n"
            await message.channel.send(reply)
            
        if message.content == "Yo yo yo cringelbot":
            await message.channel.send(f"Wassap crazy crew! I'm just here to bring the vibes (and the chips) I'm ready to become a core member of this group, I heard there was an opening")

        if message.content.startswith("!parrot "):
            await message.channel.send(message.content[8:])

        if message.content.startswith("!playalbum "):
            guild_id = initialise_globals(message)
            voice = message.guild.voice_client
            query = message.content.split(" ", 1)[1]

            if not voice:
                if message.author.voice:
                    channel = message.author.voice.channel
                    await channel.connect()
                    if silent[guild_id] == 0:
                        await message.channel.send("Joined the voice channel.")
                    voice = message.guild.voice_client
                else:
                    if silent[guild_id] == 0:
                        await message.channel.send("You must be in a voice channel.")
                    return
            
            songs = search_album(query)

            if not songs:
                if silent[guild_id] == 0:
                    await message.channel.send("No songs found.")
                elif silent[guild_id] == 1:
                    await message.delete()
                return
            
            for song in songs:
                track = song
                track_id = track["id"]
                if not voice.is_playing() and not voice.is_paused():
                    url = build_stream_url(track_id)       
                    source = discord.FFmpegPCMAudio(url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
                    voice.play(source, after=lambda e:use_queue(voice, guild_id))
                    now_playing[guild_id]["title"] = track['title']
                    now_playing[guild_id]["artist"] = track['artist']
                    if silent[guild_id] == 0:
                        await message.channel.send(f"Playing: {track['title']} by {track['artist']}")
                else:
                    queues[guild_id].insert(0, {"id": track_id, "title": track['title'], "artist": track['artist']})
                    if silent[guild_id] == 0:
                        await message.channel.send(f"Added: {track['title']} by {track['artist']} to queue. Position: {len(queues[guild_id])}")
            if silent[guild_id] == 1:
                await message.delete()

        if message.content == ("!silent"):
            guild_id = initialise_globals(message)
            if silent[guild_id] == 1:
                silent[guild_id] = 0
                await message.add_reaction("✅")
                await message.channel.send(f"Silent mode off.")
            else:
                silent[guild_id] = 1
                await message.add_reaction("✅")
                await message.delete(delay=5)

        if message.content == ("!playalbum"):
            return

        if message.content.startswith("!playrandom"):
            guild_id = initialise_globals(message)
            voice = message.guild.voice_client
            try:
                size = int(message.content.split(" ", 1)[1])
            except (IndexError, ValueError):
                size = None

            if not voice:
                if message.author.voice:
                    channel = message.author.voice.channel
                    await channel.connect()
                    if silent[guild_id] == 0:
                        await message.channel.send("Joined the voice channel.")
                    voice = message.guild.voice_client
                else:
                    if silent[guild_id] == 0:
                        await message.channel.send("You must be in a voice channel.")
                    return
            
            songs = search_random(size)

            if not songs:
                if silent[guild_id] == 0:
                    await message.channel.send("No songs found.")
                elif silent[guild_id] == 1:
                    await message.delete()
                return
            
            for song in songs:
                track = song
                track_id = track["id"]
                if not voice.is_playing() and not voice.is_paused():
                    url = build_stream_url(track_id)       
                    source = discord.FFmpegPCMAudio(url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
                    voice.play(source, after=lambda e:use_queue(voice, guild_id))
                    now_playing[guild_id]["title"] = track['title']
                    now_playing[guild_id]["artist"] = track['artist']
                    if silent[guild_id] == 0:
                        await message.channel.send(f"Playing: {track['title']} by {track['artist']}")
                else:
                    queues[guild_id].insert(0, {"id": track_id, "title": track['title'], "artist": track['artist']})
                    if silent[guild_id] == 0:
                        await message.channel.send(f"Added: {track['title']} by {track['artist']} to queue. Position: {len(queues[guild_id])}")
            if silent[guild_id] == 1:
                await message.delete()           

        

intents = discord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run(os.getenv("DISCORD_BOT_TOKEN"))