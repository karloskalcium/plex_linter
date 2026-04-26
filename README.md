[![made-with-python](https://img.shields.io/badge/Made%20with-Python-blue.svg?style=flat-square)](https://www.python.org/)
[![LICENSE](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/karloskalcium/plex_linter/refs/heads/master/LICENSE)
[![PYTHON](https://img.shields.io/badge/python-3.14-orange.svg)](https://docs.python.org/3.14/index.html)

# Introduction

Plex Linter is a python script that looks for various potential issues in your library, such as

- Duplicate album titles (for albums that have been incorrectly split)
- Duplicate artists (for artists that have been split)
- Tracks without titles (sometimes Plex metadata deletes track titles)
- Tracks linked to artists with Plex metadata that differ from what the MP3 tags say (requires running on the plex server and using the `--local` flag)
  - Note that the linter only works for music libraries currently

## Install

### With pipx (recommended, no clone needed)

```bash
pipx install git+https://github.com/karloskalcium/plex_linter.git
```

### From source (for development)

Requirements: Python 3.14, [uv](https://docs.astral.sh/uv/), [just](https://just.systems/)

```bash
git clone https://github.com/karloskalcium/plex_linter
cd plex_linter
just install
```

## Usage

Start `plex_linter` — it will check for a config file at `~/.plex_linter/plex_linter.toml`, create one if it doesn't exist, and prompt for your Plex server URL and credentials.

```bash
plex_linter
```

To check for mismatched tags (requires running on the Plex server with access to media files):

```bash
plex_linter --local
```

When running from source, prefix commands with `uv run`:

```bash
uv run plex_linter
uv run plex_linter --local
```

## Configuration

### Sample

```toml
# plex_linter.toml
[server]
server_url = "http://plex.your-server.com"
server_token = "{your-X-Plex-Token}"

[content]
libraries = [
    "Music",
    "Audiobooks"
]
```

### Plex

#### Plex Libraries

1. Go to Plex and get all the names of your Plex Music Libraries you want to run the linter on

   - Example Library:

     ![](https://i.imgur.com/JFRTD1m.png)

1. Under `libraries`, type in the Plex *Library Name* (exactly)

1. Note that the linter only works for music libraries currently

#### Plex Server URL

- Your Plex server's URL
  - This can be any format (e.g. <http://localhost:32400>, <https://plex.domain.ltd>)

#### Plex Token

1. Obtain a Plex Access Token:

   - Fill in the Plex URL and Plex login credentials, at the prompt, on first run. This only occurs when there is no valid `plex_linter.toml` present.

     or

   - Visit https://support.plex.tv/hc/en-us/articles/204059436-Finding-an-authentication-token-X-Plex-Token

______________________________________________________________________

## Inspiration

This project started as a fork of https://github.com/l3uddz/plex_dupefinder and used a lot of that code as a starting point.
