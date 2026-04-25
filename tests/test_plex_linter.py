from unittest.mock import MagicMock, patch

from plex_linter.plex_linter import (
    get_album_dupes,
    get_artist_dupes,
    get_mismatched_artists,
    get_tracks_without_titles,
)

from .conftest import make_album, make_section, make_track


class TestMutagenReturnsNone:
    """Bug: mutagen.File returns None for unrecognized formats, causing AttributeError."""

    @patch("plex_linter.plex_linter.track", side_effect=lambda iterable, *a, **kw: iterable)
    @patch("plex_linter.plex_linter.mutagen.File", return_value=None)
    def test_mutagen_returns_none_skips_track(self, mock_file, mock_track):
        t = make_track("Song", 1, "Album", "Artist", "/music/Artist/Album/song.wav")
        a = make_album("Album", "Artist", tracks=[t])
        section = make_section(albums=[a])

        result = get_mismatched_artists(section)

        assert result["albumartistsort-set"] == []
        assert result["artist-mismatch"] == []
        assert result["various-artists-mismatch"] == []


class TestGetAlbumDupes:
    def test_no_albums(self):
        section = make_section()

        result = get_album_dupes(section)

        assert result == {}

    def test_all_unique(self):
        albums = [make_album("A", "Artist1"), make_album("B", "Artist2"), make_album("C", "Artist3")]
        section = make_section(albums=albums)

        result = get_album_dupes(section)

        assert result == {}

    def test_single_dupe_pair(self):
        a1 = make_album("Same Title", "Artist1")
        a2 = make_album("Same Title", "Artist2")
        section = make_section(albums=[a1, a2])

        result = get_album_dupes(section)

        assert list(result.keys()) == ["Same Title"]
        assert result["Same Title"] == [a1, a2]


class TestGetArtistDupes:
    def test_no_artists(self):
        section = make_section()

        result = get_artist_dupes(section)

        assert result == []

    def test_all_unique(self):
        artists = [MagicMock(title="A"), MagicMock(title="B"), MagicMock(title="C")]
        section = make_section(artists=artists)

        result = get_artist_dupes(section)

        assert result == []

    def test_single_duplicate(self):
        artists = [MagicMock(title="Duped"), MagicMock(title="Duped"), MagicMock(title="Unique")]
        section = make_section(artists=artists)

        result = get_artist_dupes(section)

        assert result == ["Duped"]


class TestGetTracksWithoutTitles:
    def test_no_tracks(self):
        section = make_section()

        result = get_tracks_without_titles(section)

        assert result == []

    def test_single_track_returns_tuple(self):
        t = make_track("", 1, "Album", "Artist")
        section = make_section(tracks=[t])

        result = get_tracks_without_titles(section)

        assert len(result) == 1
        assert result == [(1, "Album", "Artist")]


class TestGetMismatchedArtists:
    @patch("plex_linter.plex_linter.track", side_effect=lambda iterable, *a, **kw: iterable)
    @patch("plex_linter.plex_linter.mutagen.File")
    def test_clean_track(self, mock_file, mock_track):
        mock_file.return_value = {"albumartist": ["Artist"], "artist": ["Artist"], "albumartistsort": [""]}
        t = make_track("Song", 1, "Album", "Artist", "/music/Artist/Album/song.mp3")
        a = make_album("Album", "Artist", tracks=[t])
        section = make_section(albums=[a])

        result = get_mismatched_artists(section)

        assert result["albumartistsort-set"] == []
        assert result["artist-mismatch"] == []
        assert result["various-artists-mismatch"] == []

    @patch("plex_linter.plex_linter.track", side_effect=lambda iterable, *a, **kw: iterable)
    @patch("plex_linter.plex_linter.mutagen.File")
    def test_albumartistsort_set(self, mock_file, mock_track):
        mock_file.return_value = {"albumartist": ["Artist"], "artist": ["Artist"], "albumartistsort": ["Artist"]}
        t = make_track("Song", 1, "Album", "Artist", "/music/Artist/Album/song.mp3")
        a = make_album("Album", "Artist", tracks=[t])
        section = make_section(albums=[a])

        result = get_mismatched_artists(section)

        assert len(result["albumartistsort-set"]) == 1
        assert result["artist-mismatch"] == []
        assert result["various-artists-mismatch"] == []

    @patch("plex_linter.plex_linter.track", side_effect=lambda iterable, *a, **kw: iterable)
    @patch("plex_linter.plex_linter.mutagen.File")
    def test_artist_mismatch(self, mock_file, mock_track):
        mock_file.return_value = {"albumartist": ["OtherArtist"], "artist": ["OtherArtist"], "albumartistsort": [""]}
        t = make_track("Song", 1, "Album", "Artist", "/music/Artist/Album/song.mp3")
        a = make_album("Album", "Artist", tracks=[t])
        section = make_section(albums=[a])

        result = get_mismatched_artists(section)

        assert result["albumartistsort-set"] == []
        assert len(result["artist-mismatch"]) == 1
        assert result["various-artists-mismatch"] == []

    @patch("plex_linter.plex_linter.track", side_effect=lambda iterable, *a, **kw: iterable)
    @patch("plex_linter.plex_linter.mutagen.File")
    def test_artist_tag_saves_from_mismatch(self, mock_file, mock_track):
        mock_file.return_value = {"albumartist": ["Wrong"], "artist": ["Artist"], "albumartistsort": [""]}
        t = make_track("Song", 1, "Album", "Artist", "/music/Artist/Album/song.mp3")
        a = make_album("Album", "Artist", tracks=[t])
        section = make_section(albums=[a])

        result = get_mismatched_artists(section)

        assert result["albumartistsort-set"] == []
        assert result["artist-mismatch"] == []
        assert result["various-artists-mismatch"] == []

    @patch("plex_linter.plex_linter.track", side_effect=lambda iterable, *a, **kw: iterable)
    @patch("plex_linter.plex_linter.mutagen.File")
    def test_various_artists_plex_flag(self, mock_file, mock_track):
        mock_file.return_value = {"albumartist": ["SomeArtist"], "artist": ["SomeArtist"], "albumartistsort": [""]}
        t = make_track("Song", 1, "Album", "Various Artists", "/music/Various Artists/Album/song.mp3")
        a = make_album("Album", "Various Artists", tracks=[t])
        section = make_section(albums=[a])

        result = get_mismatched_artists(section)

        assert result["albumartistsort-set"] == []
        assert result["artist-mismatch"] == []
        assert len(result["various-artists-mismatch"]) == 1

    @patch("plex_linter.plex_linter.track", side_effect=lambda iterable, *a, **kw: iterable)
    @patch("plex_linter.plex_linter.mutagen.File")
    def test_compilations_folder(self, mock_file, mock_track):
        mock_file.return_value = {"albumartist": ["SomeArtist"], "artist": ["SomeArtist"], "albumartistsort": [""]}
        t = make_track("Song", 1, "Album", "SomeArtist", "/music/Compilations/Album/song.mp3")
        a = make_album("Album", "SomeArtist", tracks=[t])
        section = make_section(albums=[a])

        result = get_mismatched_artists(section)

        assert result["albumartistsort-set"] == []
        assert result["artist-mismatch"] == []
        assert len(result["various-artists-mismatch"]) == 1

    @patch("plex_linter.plex_linter.track", side_effect=lambda iterable, *a, **kw: iterable)
    @patch("plex_linter.plex_linter.mutagen.File")
    def test_various_artists_correct(self, mock_file, mock_track):
        mock_file.return_value = {
            "albumartist": ["Various Artists"],
            "artist": ["Various Artists"],
            "albumartistsort": [""],
        }
        t = make_track("Song", 1, "Album", "Various Artists", "/music/Various Artists/Album/song.mp3")
        a = make_album("Album", "Various Artists", tracks=[t])
        section = make_section(albums=[a])

        result = get_mismatched_artists(section)

        assert result["albumartistsort-set"] == []
        assert result["artist-mismatch"] == []
        assert result["various-artists-mismatch"] == []
