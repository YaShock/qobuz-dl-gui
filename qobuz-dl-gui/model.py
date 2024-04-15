from collections import namedtuple
from enum import Enum


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


def parse_str(s_type: str, s: str) -> namedtuple:
    # TODO: error handling
    if s_type == "album":
        vals = s.split(" - ")
        dur_quality = vals[2].split(" ")
        return Album(vals[0], vals[1], dur_quality[0], dur_quality[1])
    elif s_type == "artist":
        vals = s.split(" - ")
        return Artist(vals[0], vals[1])
    elif s_type == "track":
        vals = s.split(" - ")
        dur_quality = vals[2].split(" ")
        return Track(vals[0], vals[1], dur_quality[0], dur_quality[1])
    elif s_type == "playlist":
        vals = s.split(" - ")
        return Playlist(vals[0], vals[1])
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

