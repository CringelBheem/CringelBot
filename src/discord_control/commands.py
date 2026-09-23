from state import get_guild
from discord_control.responses import silent_response, error_response, join_check
from music.player import add_track
from navidrome.api import search_navidrome, search_album, search_random

async def join(message):
    guild = get_guild(message.guild.id)
    voice = message.guild.voice_client
    if not voice:
        joined = await join_check(message, guild)

        if not joined:
            return
    await silent_response(guild, message)

async def leave(message):
    guild = get_guild(message.guild.id)
    if guild.now_playing:
        guild.now_playing["title"] = ""
        guild.now_playing["artist"]= ""
        guild.now_playing["track_id"]= ""
    if guild.queue:
        guild.queue.clear()
    if message.guild.voice_client:
        await message.guild.voice_client.disconnect()
        if guild.silent == 0:
            await message.channel.send("Left the voice channel.")
    await silent_response(guild, message)
    
async def play(message):
    guild = get_guild(message.guild.id)
    voice = message.guild.voice_client
    query = message.content.split(" ", 1)[1]

    if not voice:
        joined = await join_check(message, guild)
        if not joined:
            return
        voice = message.guild.voice_client
    
    results = search_navidrome(query, "search2")
    songs = results.get("song", [])

    if not songs:
        await error_response("No songs found.", guild, message)
        return

    track = songs[0]
    await add_track(voice, message, guild, track)
    await silent_response(guild, message)
        
async def search(message):
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

async def skip(message):
    guild = get_guild(message.guild.id)
    if guild.silent == 0:
        await message.channel.send(f"Skipping track.")
    voice = message.guild.voice_client
    if voice:
        voice.stop()
    await silent_response(guild, message)

async def stop(message):
    guild = get_guild(message.guild.id)
    if guild.silent == 0:
        await message.channel.send(f"Stopped all songs.")
    if guild.queue:
        guild.queue.clear()
    voice = message.guild.voice_client
    if voice:
        voice.stop()
    await silent_response(guild, message)

async def pause(message):
    guild = get_guild(message.guild.id)
    if guild.silent == 0:
        await message.channel.send(f"Paused.")
    voice = message.guild.voice_client
    if voice:
        voice.pause()
    await silent_response(guild, message)

async def resume(message):
    guild = get_guild(message.guild.id)
    if guild.silent == 0:
        await message.channel.send(f"Resuming.")
    voice = message.guild.voice_client
    if voice:
        voice.resume()
    await silent_response(guild, message)

async def playing(message):
    guild = get_guild(message.guild.id)
    if (not guild.now_playing or guild.now_playing["title"] == ""):
        await message.channel.send("Nothing is currently playing.")
        return
    await message.channel.send(f"**Currently playing**: {guild.now_playing['title']} by {guild.now_playing['artist']}.")

async def queue(message):
    guild = get_guild(message.guild.id)
    if (not guild.now_playing or guild.now_playing["title"] == ""):
        await message.channel.send("Nothing is currently playing.")
        return
    reply = f"**Currently playing: ** {guild.now_playing['title']} by {guild.now_playing['artist']}.\n"
    for i, track in enumerate(reversed(guild.queue)):
        reply += f"**{i+1}: ** {track['title']} by {track['artist']}.\n"
    await message.channel.send(reply)
    
async def parrot(message):
    await message.channel.send(message.content[8:])
    await message.delete()

async def play_album(message):
    guild = get_guild(message.guild.id)
    voice = message.guild.voice_client
    query = message.content.split(" ", 1)[1]

    if not voice:
        joined = await join_check(message, guild)
        if not joined:
            return
        voice = message.guild.voice_client
    
    songs = search_album(query)

    if not songs:
        await error_response("No songs found.", guild, message)
        return
    
    for song in songs:
        await add_track(voice, message, guild, song)
    await silent_response(guild, message)

async def silent(message):
    guild = get_guild(message.guild.id)
    if guild.silent == 1:
        guild.silent = 0
        await message.add_reaction("✅")
        await message.channel.send(f"Silent mode off.")
    else:
        guild.silent = 1
        await message.add_reaction("✅")
        await message.delete(delay=2)

async def play_random_album(message):
    guild = get_guild(message.guild.id)
    voice = message.guild.voice_client

    if not voice:
        joined = await join_check(message, guild)
        if not joined:
            return
        voice = message.guild.voice_client
    
    randsong = search_random(1)

    if not randsong:
        await error_response("No albums found.", guild, message)
        return
    
    album = randsong[0]["album"]

    songs = search_album(album)

    if not songs:
        await error_response("No songs found.", guild, message)
        return
    
    for song in songs:
        await add_track(voice, message, guild, song)
    await silent_response(guild, message)

async def play_random(message):
    guild = get_guild(message.guild.id)
    voice = message.guild.voice_client
    try:
        size = int(message.content.split(" ", 1)[1])
    except (IndexError, ValueError):
        size = None

    if not voice:
        joined = await join_check(message, guild)
        if not joined:
            return
        voice = message.guild.voice_client
    
    songs = search_random(size)

    if not songs:
        await error_response("No songs found.", guild, message)
        return
    
    for song in songs:
        await add_track(voice, message, guild, song)
    await silent_response(guild, message)

async def remove_item(message):
    guild = get_guild(message.guild.id)
    try:
        queue_ind = int(message.content.split(" ", 1)[1])
    except (IndexError, ValueError):
        queue_ind = None
        await error_response("No valid index.", guild, message)
        return
    try:
        length = len(guild.queue)
        removed_item = guild.queue.pop(length - queue_ind)
        if guild.silent == 0:
            await message.channel.send(f"Removed: {removed_item['title']} by {removed_item['artist']} from queue.")
        else:
            await silent_response(guild, message)
    except  (IndexError, ValueError):
        await error_response("No valid index.", guild, message)
        return
    
    