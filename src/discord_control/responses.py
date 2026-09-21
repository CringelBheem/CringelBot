
async def silent_response(guild, message):
    if guild.silent == 1:
        await message.add_reaction("✅")
        await message.delete(delay=2)

async def error_response(text, guild, message):
    if guild.silent == 0:
        await message.channel.send(text)
    elif guild.silent == 1:
        await message.add_reaction("❌")
        await message.delete(delay=2)

async def join_check(message, guild):
    if message.author.voice:
        channel = message.author.voice.channel
        await channel.connect()
        if guild.silent == 0:
            await message.channel.send("Joined the voice channel.")
        return True
    else:
        await error_response("You must be in a voice channel.", guild, message)
        return False

