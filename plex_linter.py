#!/usr/bin/env python3
import logging
import os
import sys
from collections import defaultdict, Counter
from config import cfg
from pprint import pprint
from plexapi.server import PlexServer

############################################################
# INIT
############################################################

# Setup logger
log_filename = os.path.join(
    os.path.dirname(
        os.path.realpath(
            sys.argv[0])),
    'activity.log')
logging.basicConfig(
    filename=log_filename,
    level=logging.DEBUG,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logging.getLogger('urllib3.connectionpool').disabled = True
log = logging.getLogger("Plex_Linter")

# Setup PlexServer object
try:
    plex = PlexServer(cfg.PLEX_SERVER, cfg.PLEX_TOKEN)
except BaseException:
    log.exception("Exception connecting to server %r with token %r",
                  cfg.PLEX_SERVER, cfg.PLEX_TOKEN)
    print("Exception connecting to %s with token: %s" % (cfg.PLEX_SERVER,
                                                         cfg.PLEX_TOKEN))
    exit(1)


############################################################
# PLEX METHODS
############################################################

def get_album_dupes(plex_section_name) -> dict:
    section = plex.library.section(plex_section_name)
    albums = section.albums()
    album_dict = defaultdict(list)
    for a in albums:
        album_dict[a.title].append(a)
    result = {k: v for (k, v) in album_dict.items() if len(v) > 1}
    return result


def get_artist_dupes(plex_section_name) -> list:
    section = plex.library.section(plex_section_name)
    artists_names = [a.title for a in section.searchArtists()]
    count = Counter(artists_names)
    result = [k for k, v in count.items() if v > 1]
    return result


def get_tracks_without_titles(plex_section_name) -> list:
    section = plex.library.section(plex_section_name)
    albums = section.albums()
    result = []
    for a in albums:
        result.extend([(t.index, t.album().title, t.artist().title) for
                       t in a.tracks() if not t.title.strip()])
    return result


############################################################
# MISC METHODS
############################################################

def print_dupe_list(dupes: list, header_message: str) -> None:
        print(header_message)
        if len(dupes) > 0:
            pprint(dupes)


############################################################
# MAIN
############################################################
def main() -> None:
    print("Starting to lint...")
    for section in cfg.PLEX_LIBRARIES:
        dupes = get_album_dupes(section)
        print("Found %d album name dupes for section %r" %
              (len(dupes), section))
        for key in dupes:
            for value in dupes[key]:
                print("Title: '" + key + "', Artist: " + value.parentTitle)

        dupes = get_artist_dupes(section)
        print_dupe_list(dupes, "Found %d artist name dupes for section %r" %
                        (len(dupes), section))

        notitles = get_tracks_without_titles(section)
        print_dupe_list(dupes, "Found %d tracks without titles in section %r" %
                        (len(notitles), section))

    print("Done!")


if __name__ == "__main__":
    main()
