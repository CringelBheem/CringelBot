class GuildState:
    def __init__(self):
        self.queue = []
        self.silent = 0
        self.now_playing = {
            "title": "",
            "artist": "",
            "track_id": ""

        }

guilds = {}

def get_guild(guild_id):
    if guild_id not in guilds:
        guilds[guild_id] = GuildState()
    return guilds[guild_id]