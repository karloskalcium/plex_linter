#!/usr/bin/env python3
import logging
import os
import sys
from collections import Counter, defaultdict
from pprint import pformat
from rich.progress import track
import line_profiler
from mutagen import File, MutagenError
from rich import print

from .config import get_plex_server

# Setup logger
log_filename = os.path.join(os.path.dirname(os.path.realpath(sys.argv[0])), "activity.log")
logging.basicConfig(
    filename=log_filename, level=logging.DEBUG, format="[%(asctime)s] %(levelname)s - %(message)s", datefmt="%H:%M:%S"
)
logging.getLogger("urllib3.connectionpool").disabled = True
log = logging.getLogger("plex_linter")


############################################################
# PLEX METHODS
############################################################

@line_profiler.profile
def get_album_dupes(section) -> dict:
    albums = section.albums()
    album_dict = defaultdict(list)
    # for i in track(range(20), description="Processing..."):

    for a in track(albums, description="Processing album dupes..."):
        album_dict[a.title].append(a)
    result = {k: v for (k, v) in album_dict.items() if len(v) > 1}
    return result

@line_profiler.profile
def get_artist_dupes(section) -> list:
    artists_names = [a.title for a in section.searchArtists()]
    count = Counter(artists_names)
    result = [k for k, v in count.items() if v > 1]
    return result

@line_profiler.profile
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
                    tag_album_artist = tags.get("albumartist", [""])[0]
                    tag_artist = tags.get("artist", [""])[0]
                    if tag_album_artist != album_artist and tag_artist != album_artist:
                        result.append(
                            (
                                t.title,
                                t.album().title,
                                "plex-album-artist: " + album_artist,
                                "tag-album-artist: " + tag_album_artist,
                                "tag-artist:" + tag_artist,
                            )
                        )
                except MutagenError:
                    log.exception(f"Exception caught trying to read {file_name}")

    return result


############################################################
# MISC METHODS
############################################################


def print_list(my_list: list, header_message: str) -> None:
    print(header_message)
    if len(my_list) > 0:
        print(pformat(my_list, width=160))


def app() -> None:
    print("Starting to lint...")
    plex, config = get_plex_server()
    for section_name in config["content"]["libraries"]:
        section = plex.library.section(section_name)
        dupes = get_album_dupes(section)
        print(f"Found {len(dupes)} album name dupes in library {section_name}")
        for key in dupes:
            for value in dupes[key]:
                print("Title: '" + key + "', Artist: " + value.parentTitle)

        dupes = get_artist_dupes(section)
        print_list(dupes, f"Found {len(dupes)} artist name dupes in library {section_name}")

        no_titles = get_tracks_without_titles(section)
        print_list(no_titles, f"Found {len(no_titles)} tracks without titles in library {section_name}")

        # print("Finding wrong artists")
        # wrong_artists = get_different_artists(section)
        # print_list(wrong_artists, "Found %d tracks with potentially the wrong "
        #            " artists in section %r" % (len(wrong_artists),
        #                                        section_name))

    print("Done!")


def main():
    app()


# needed so we can invoke within IDE
if __name__ == "__main__":
    main()
