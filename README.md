[![made-with-python](https://img.shields.io/badge/Made%20with-Python-blue.svg?style=flat-square)](https://www.python.org/)
[![LICENSE](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/karloskalcium/md2enex/master/LICENSE)
[![PYTHON](https://img.shields.io/badge/python-3.12-orange.svg)](https://docs.python.org/3.12/index.html)

# Introduction

Plex Linter is a python script that looks for various potential issues in your library, such as

- Duplicate album titles (for albums that have been incorrectly split)
- Duplicate artists (for artists that have been split)
- Tracks without titles (sometimes Plex metadata deletes track titles)
- Tracks linked to artists with Plex metadata that differ from what the MP3 tags say (requires running on the plex server and using the `--local` flag)
  - Note that the linter only works for music libraries currently

## Setup

### Requirements

1. Python 3.12+
1. [Poetry](https://python-poetry.org/)

_Note: Steps below are for OSX (other operating systems will require tweaking to the steps)_

1. Install [Python 3.12](https://www.python.org/downloads/release/python-3123/), you can use [asdf](https://asdf-vm.com/) to manage multiple python versions if needed

1. Install `poetry` according to the [instructions](https://python-poetry.org/docs/#installation)

1. Clone the `plex_linter` repo

   ```commandline
   git clone https://github.com/karloskalcium/plex_linter
   ```

1. Setup the virtual environment

   ```commandline
   cd plex_linter
   make install
   ```

## Usage

1. Start the `plex_linter`, it will check for a config file, create a new one if it doesn't exist, and ask you to fill your Plex server URL and credentials to generate a Plex Access Token

   ```commandline
   poetry run plex_linter
   ```

1. If you are running on the plex server and want to check for mismatched tags, pass the `--local` flag as follows:

   ```commandline
   poetry run plex_linter --local
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
