#!/usr/bin/env python3
import logging
import os
import sys
from collections import Counter, defaultdict
from pprint import pprint

from mutagen import File, MutagenError
from plexapi.server import PlexServer

from .config import cfg

############################################################
# INIT
############################################################

# Setup logger
log_filename = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "activity.log")
logging.basicConfig(
    filename=log_filename, level=logging.DEBUG, format="[%(asctime)s] %(levelname)s - %(message)s", datefmt="%H:%M:%S"
)
logging.getLogger("urllib3.connectionpool").disabled = True
log = logging.getLogger("Plex_Linter")

# Setup PlexServer object
try:
    plex = PlexServer(cfg.PLEX_SERVER, cfg.PLEX_TOKEN)
except BaseException:
    log.exception("Exception connecting to server %r with token %r", cfg.PLEX_SERVER, cfg.PLEX_TOKEN)
    print(f"Exception connecting to {cfg.PLEX_SERVER} with token: {cfg.PLEX_TOKEN}")
    exit(1)


############################################################
# PLEX METHODS
############################################################


def get_album_dupes(section) -> dict:
    albums = section.albums()
    album_dict = defaultdict(list)
    for a in albums:
        album_dict[a.title].append(a)
    result = {k: v for (k, v) in album_dict.items() if len(v) > 1}
    return result


def get_artist_dupes(section) -> list:
    artists_names = [a.title for a in section.searchArtists()]
    count = Counter(artists_names)
    result = [k for k, v in count.items() if v > 1]
    return result


def get_tracks_without_titles(section) -> list:
    albums = section.albums()
    result = []
    for a in albums:
        result.extend([(t.index, t.album().title, t.artist().title) for t in a.tracks() if not t.title.strip()])
    return result


def get_different_artists(section) -> list:
    albums = section.albums()
    result = []
    count = 0
    for a in albums:
        album_artist = a.artist().title
        if album_artist == "Various Artists":
            pass
        else:
            tracks = a.tracks()
            for t in tracks:
                count += 1
                if count % 100 == 0:
                    print(".", end="", flush=True)
                file_name = next(t.iterParts()).file
                try:
                    tags = File(file_name, easy=True)
                    tag_albumartist = tags.get("albumartist", [""])[0]
                    tag_artist = tags.get("artist", [""])[0]
                    if tag_albumartist != album_artist and tag_artist != album_artist:
                        result.append(
                            (
                                t.title,
                                t.album().title,
                                "plex-album-artist: " + album_artist,
                                "tag-album-artist: " + tag_albumartist,
                                "tag-artist:" + tag_artist,
                            )
                        )
                except MutagenError as err:
                    pprint(err)
                    print(f"Exception caught trying to read {file_name}")
    return result


############################################################
# MISC METHODS
############################################################


def print_list(my_list: list, header_message: str) -> None:
    print(header_message)
    if len(my_list) > 0:
        pprint(my_list, width=160)


############################################################
# MAIN
############################################################
def main() -> None:
    print("Starting to lint...")
    for section_name in cfg.PLEX_LIBRARIES:
        section = plex.library.section(section_name)
        dupes = get_album_dupes(section)
        print("Found %d album name dupes for section %r" % (len(dupes), section_name))
        for key in dupes:
            for value in dupes[key]:
                print("Title: '" + key + "', Artist: " + value.parentTitle)

        dupes = get_artist_dupes(section)
        print_list(dupes, "Found %d artist name dupes for section %r" % (len(dupes), section_name))

        notitles = get_tracks_without_titles(section)
        print_list(notitles, "Found %d tracks without titles in section %r" % (len(notitles), section_name))

        # print("Finding wrong artists")
        # wrong_artists = get_different_artists(section)
        # print_list(wrong_artists, "Found %d tracks with potentially the wrong "
        #            " artists in section %r" % (len(wrong_artists),
        #                                        section_name))

    print("Done!")


if __name__ == "__main__":
    main()
