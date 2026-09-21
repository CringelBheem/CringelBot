import  os
import requests
import hashlib
import random
import string
from dotenv import load_dotenv

load_dotenv()

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
    album_id = albums[0]["id"]


    params = {
            "id": album_id,
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

def search_similar(track_id, size):
    url = os.getenv("NAVIDROME_URL")+f"/rest/getSimilarSongs"

    token, salt = generate_token(os.getenv("NAVIDROME_PASSWORD"))

    params = {
            "id": track_id,
            "count": size if size else 1,
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
        return data["subsonic-response"]["similarSongs"]["song"]
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

