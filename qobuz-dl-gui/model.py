from collections import namedtuple
from enum import Enum
from qobuz_dl.utils import format_duration


Album = namedtuple("Album", ["artist", "name", "duration", "quality"])
Artist = namedtuple("Artist", ["name", "releases"])
Track = namedtuple("Track", ["artist", "name", "duration", "quality"])
Playlist = namedtuple("Playlist", ["name", "releases"])

# READY: initial
# QUEUED: added to dl queue
# IN_PROGRESS: being downloaded
# DONE: download finished
class DownloadStatus(Enum):
    READY, QUEUED, IN_PROGRESS, DONE = range(4)

class DownloadItem:
    def __init__(self, typ, desc, url, status):
        self.typ = typ
        self.desc = desc
        self.url = url
        self.status = status

# DownloadItem = namedtuple("DownloadItem", ["type", "desc", "url", "status"])


def parse_str(s_type: str, data: dict) -> namedtuple:
    if s_type == "album":
        artist_name = data["artist"]["name"]
        duration = format_duration(data["duration"])
        quality = "HI-RES" if data["hires_streamable"] else "LOSSLESS"
        return Album(artist_name, data["title"], duration, quality)
    elif s_type == "artist":
        return Artist(data["name"], str(data["albums_count"]))
    elif s_type == "track":
        performer = data["performer"]["name"]
        duration = format_duration(data["duration"])
        quality = "HI-RES" if data["hires_streamable"] else "LOSSLESS"
        return Track(performer, data["title"], duration, quality)
    elif s_type == "playlist":
        return Playlist(data["name"], str(data["tracks_count"]))
    else:
        raise Exception("parse_str: unknown search type")

# class ModelBase:
#     display = ""
#     name = ""

#     def parse(s: str):
#         raise Exception("Unsupported type")

# class Album:
#     display = "Album"
#     name = "album"

#     def __init__(self, artist: str, name: str, duration: str, quality: str):
#         self.artist = artist
#         self.name = name
#         self.duration = duration
#         self.quality = quality
#     props = ['artist', 'name', 'duration', 'quality']

# class Artist:
#     pass

# class Track:
#     pass

# class Playlist:
#     pass

