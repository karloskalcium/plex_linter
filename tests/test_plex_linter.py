from unittest.mock import patch

from plex_linter.plex_linter import get_mismatched_artists, get_tracks_without_titles

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


class TestTrackCountBug:
    """Bug: get_tracks_without_titles uses extend instead of append, inflating len() by 3x."""

    def test_single_track_returns_tuple(self):
        t = make_track("", 1, "Album", "Artist")
        section = make_section(tracks=[t])

        result = get_tracks_without_titles(section)

        assert len(result) == 1
        assert result == [(1, "Album", "Artist")]
