from navidrome.api import build_stream_url
import discord
from discord import FFmpegPCMAudio

def use_queue(voice, guild):
    if len(guild.queue) > 0:
        next_queue = guild.queue.pop()
        next_track = next_queue["id"]
        guild.now_playing["title"] = next_queue["title"]
        guild.now_playing["artist"] = next_queue["artist"]
        guild.now_playing["track_id"] = next_queue["id"]
        url = build_stream_url(next_track)         
        source = discord.FFmpegPCMAudio(url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
        voice.play(source, after=lambda e:use_queue(voice, guild))
    else:
        if guild.now_playing:
            guild.now_playing["title"] = ""
            guild.now_playing["artist"]= ""
            guild.now_playing["track_id"]= ""
        return

async def add_track(voice, message, guild, track):
    track_id = track["id"]
    if not voice.is_playing() and not voice.is_paused():
        url = build_stream_url(track_id)       
        source = discord.FFmpegPCMAudio(url, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5", options="-vn")
        voice.play(source, after=lambda e:use_queue(voice, guild))
        guild.now_playing["title"] = track['title']
        guild.now_playing["artist"] = track['artist']
        guild.now_playing["track_id"] = track_id
        if guild.silent == 0:
            await message.channel.send(f"Playing: {track['title']} by {track['artist']}")
    else:
        guild.queue.insert(0, {"id": track_id, "title": track['title'], "artist": track['artist']})
        if guild.silent == 0:
            await message.channel.send(f"Added: {track['title']} by {track['artist']} to queue. Position: {len(guild.queue)}")
