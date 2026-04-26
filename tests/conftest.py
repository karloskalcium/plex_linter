from unittest.mock import MagicMock


def make_part(file_path):
    p = MagicMock()
    p.file = file_path
    return p


def make_track(title, index, album_title, artist_title, file_path="/music/Artist/Album/track.mp3"):
    t = MagicMock()
    t.title = title
    t.index = index
    t.album.return_value.title = album_title
    t.artist.return_value.title = artist_title
    t.iterParts.side_effect = lambda: iter([make_part(file_path)])
    return t


def make_album(title, artist_title, tracks=None):
    a = MagicMock()
    a.title = title
    a.artist.return_value.title = artist_title
    a.tracks.return_value = tracks or []
    return a


def make_section(albums=None, artists=None, tracks=None):
    s = MagicMock()
    s.albums.return_value = albums or []
    s.searchArtists.return_value = artists or []
    s.searchTracks.return_value = tracks or []
    return s
