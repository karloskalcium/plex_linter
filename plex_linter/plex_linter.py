#!/usr/bin/env python3
import importlib.metadata
import logging
import os
from collections import Counter, defaultdict
from enum import Enum
from inspect import getsourcefile
from os.path import basename, dirname
from pprint import pformat
from typing import Annotated, Optional

import line_profiler
import mutagen
import typer
from plexapi.library import LibrarySection
from rich import print
from rich.progress import track

from ._utils import xstr
from .config import LinterConfig

# Setup Typer per https://github.com/tiangolo/typer/issues/201#issuecomment-747128376
app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, add_completion=False)


# Enum for App Configuration Constants
class AppConfig(Enum):
    APP_NAME = "plex_linter"
    APP_VERSION = importlib.metadata.version(str(APP_NAME))


# Setup logger
# Grabs current module, goes up one directory, then appends log directory to generate logfile name
log_filename = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(xstr(getsourcefile(lambda: 0))))),
    "log/" + AppConfig.APP_NAME.value + ".log",
)
logging.basicConfig(
    filename=log_filename,
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logging.getLogger("urllib3.connectionpool").disabled = True
log = logging.getLogger(__name__)


############################################################
# PLEX METHODS
############################################################


@line_profiler.profile
def get_album_dupes(section: LibrarySection) -> dict:
    albums = section.albums()
    album_dict = defaultdict(list)
    for a in albums:
        album_dict[a.title].append(a)
    result = {k: v for (k, v) in album_dict.items() if len(v) > 1}
    return result


@line_profiler.profile
def get_artist_dupes(section: LibrarySection) -> list:
    artists = section.searchArtists()
    artists_names = [a.title for a in artists]
    count = Counter(artists_names)
    result = [k for k, v in count.items() if v > 1]
    return result


@line_profiler.profile
def get_tracks_without_titles(section: LibrarySection) -> list:
    tracks = section.searchTracks(filters={"title=": ""})
    result = []
    for t in tracks:
        result.extend((t.index, t.album().title, t.artist().title))

    return result


@line_profiler.profile
def get_mismatched_artists(section: LibrarySection) -> dict:
    albums = section.albums()
    result = {"albumartistsort-set": [], "artist-mismatch": [], "various-artists-mismatch": []}
    error_count = 0
    for a in track(albums, "Checking for mismatched artists"):
        plex_album_artist = a.artist().title
        tracks = a.tracks()
        for t in tracks:
            try:
                file_name = next(t.iterParts()).file
                media_file = mutagen.File(file_name, easy=True)
                tag_album_artist = media_file.get("albumartist", [""])[0]
                tag_artist = media_file.get("artist", [""])[0]
                tag_album_artist_sort = media_file.get("albumartistsort", [""])[0]

                track_details = (
                    t.title,
                    a.title,
                    "plex-album-artist: " + plex_album_artist,
                    "tag-album-artist: " + tag_album_artist,
                    "tag-album-artist-sort: '" + tag_album_artist_sort + "'",
                    "tag-artist: " + tag_artist,
                )

                # from plex forums. apparently albumartistsort being set can cause issues
                # https://forums.plex.tv/t/various-artists-albums-tagged-as-different-random-library-artist/573618/15
                if tag_album_artist_sort != "":
                    result["albumartistsort-set"].append(track_details)

                # assuming track is in 'artistname / albumname / track.mp3"
                artist_folder_name = str(basename(dirname(dirname(file_name))))

                if (
                    plex_album_artist == "Various Artists"
                    or artist_folder_name == "Various Artists"
                    or artist_folder_name == "Compilations"
                ):
                    if plex_album_artist != "Various Artists" or tag_album_artist != "Various Artists":
                        result["various-artists-mismatch"].append(track_details)
                elif tag_album_artist != plex_album_artist and tag_artist != plex_album_artist:
                    result["artist-mismatch"].append(track_details)
            except mutagen.MutagenError:
                log.exception(f"Exception caught trying to read {file_name}")
                error_count += 1
                if error_count > 50:
                    print(
                        f"[logging.level.error]Error: {error_count} errors caught trying to access files "
                        + f"so we are giving up. Check {log_filename} for more details."
                    )
                    return result

    if error_count > 0:
        print(
            f"[logging.level.warning]Warning: {error_count} errors detected when "
            + f"trying to read files from disk. See {log_filename} for more details."
        )
    return result


############################################################
# MISC METHODS
############################################################


def print_list(my_list: list, header_message: str) -> None:
    print(header_message)
    if len(my_list) > 0:
        print(pformat(my_list, width=160))


def version_callback(value: bool):
    if value:
        print(AppConfig.APP_NAME.value + " (version " + AppConfig.APP_VERSION.value + ")")
        raise typer.Exit(code=0)


@app.command()
def cli(
    local: Annotated[
        Optional[bool],  # noqa: UP007
        typer.Option(
            "--local",
            "-l",
            help="Set if run on Plex server to check for mismatched artists (requires access to media files)",
        ),
    ] = False,
    version: Annotated[
        Optional[bool],  # noqa: UP007
        typer.Option("--version", "-v", callback=version_callback, help="Program version number"),
    ] = None,
) -> None:
    lcfg = LinterConfig()
    plex, config = lcfg.get_plex_server()
    print("Server login successful")
    lcfg.check_continue(config)
    for section_name in config["content"]["libraries"]:
        log.debug(f"Starting to lint {section_name}")
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

        if local:
            mismatched_artists = get_mismatched_artists(section)
            print_list(
                mismatched_artists["artist-mismatch"],
                f"Found {len(mismatched_artists['artist-mismatch'])} tracks with potentially "
                + f"mismatched artists in library {section_name}",
            )
            print_list(
                mismatched_artists["various-artists-mismatch"],
                f"Found {len(mismatched_artists['various-artists-mismatch'])} tracks with potentially "
                + f"bad various items tags in library {section_name}",
            )
            print_list(
                mismatched_artists["albumartistsort-set"],
                f"Found {len(mismatched_artists['albumartistsort-set'])} tracks with albumartistsort "
                + f"tag set in library {section_name}",
            )
    print("Done!")


def main():
    app()


# needed so we can invoke within IDE
if __name__ == "__main__":
    main()
