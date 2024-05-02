#!/usr/bin/env python3
import importlib.metadata
import logging
import os
from collections import Counter, defaultdict
from enum import Enum
from inspect import getsourcefile
from pprint import pformat
from typing import Annotated, Optional

import line_profiler
import mutagen
import typer
from plexapi.library import LibrarySection
from rich import print
from rich.progress import track

from ._utils import xstr
from .config import check_continue, get_plex_server

# Setup Typer per https://github.com/tiangolo/typer/issues/201#issuecomment-747128376
app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]}, add_completion=False)


# Enum for App Configuration Constants
class AppConfig(Enum):
    APP_NAME = "plex_linter"
    APP_VERSION = importlib.metadata.version(APP_NAME)


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
def get_mismatched_artists(section: LibrarySection) -> list:
    albums = section.albums()
    result = []
    error_count = 0
    for a in track(albums, "Checking for mismatched artists"):
        album_artist = a.artist().title
        if album_artist == "Various Artists":
            pass
        else:
            tracks = a.tracks()
            for t in tracks:
                file_name = next(t.iterParts()).file
                try:
                    tags = mutagen.File(file_name, easy=True)
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
    plex, config = get_plex_server()
    print("Server login successful")
    check_continue(config)
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
                mismatched_artists,
                f"Found {len(mismatched_artists)} tracks with potentially "
                + f"mismatched artists in library {section_name}",
            )

    print("Done!")


def main():
    app()


# needed so we can invoke within IDE
if __name__ == "__main__":
    main()
