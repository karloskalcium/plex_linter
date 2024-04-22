import logging
import os
import shutil
from getpass import getpass
from inspect import getsourcefile
from pprint import pformat

import plexapi.exceptions
import requests
import typer
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from tomlkit import toml_file

# Get the path of where this module lives
config_path = os.path.join(os.path.dirname(os.path.abspath(getsourcefile(lambda: 0))), "../config.toml")
template_path = os.path.join(os.path.dirname(os.path.abspath(getsourcefile(lambda: 0))), "../config.template.toml")


def plex_server_login(url: str, token: str) -> PlexServer:
    """Attempts to log into plex server, returning server if success, raises error otherwise"""
    try:
        plex = PlexServer(url, token)
    except plexapi.exceptions.Unauthorized:
        logging.error(f"Unauthorized error connecting to server {url}, check your credentials")
        raise
    except requests.exceptions.ConnectionError:
        logging.error(f"Error connecting to {url}, check the URL provided")
        raise

    return plex


def authenticate(config: toml_file.TOMLDocument) -> PlexServer:
    """Gathers url, username and password from user, and repeats until successful authentication"""
    """Server URL and valid token are placed in the config document when successful"""
    plex = None
    while True:
        url = input("Plex server URL: ")
        user = input("Plex username: ")
        password = getpass("Plex password: ")
        try:
            account = MyPlexAccount(user, password)
            token = account.authenticationToken
            plex = plex_server_login(url, token)
        except plexapi.exceptions.Unauthorized:
            logging.error("Unauthorized error connecting to Plex, check your credentials")
            continue
        except requests.exceptions.ConnectionError:
            logging.error("Error connecting, check url")
            continue

        config["server"]["server_url"] = url
        config["server"]["server_token"] = token
        break

    return plex


def get_config() -> PlexServer:
    if not os.path.exists(config_path):
        shutil.copy(template_path, config_path)

    t = toml_file.TOMLFile(config_path)
    config = t.read()
    logging.debug(pformat(config))

    plex: PlexServer = None
    if (len(config["server"]["server_url"]) == 0) or (len(config["server"]["server_token"]) == 0):
        plex = authenticate(config)
    else:
        plex = plex_server_login(config["server"]["server_url"], config["server"]["server_token"])
        if plex is None:
            plex = authenticate(config)

    # write config file back out to disk
    t.write(config)
    checkcontinue(config)
    return plex


def checkcontinue(config: toml_file.TOMLDocument):
    """Prints out list of libraries, gives user the option to exit or continue"""
    typer.echo("Current libraries are:")
    for lib in config["content"]["libraries"]:
        typer.echo(f"  * {lib}")

    typer.echo(f"If these aren't correct, edit {os.path.abspath(config_path)} to add the target libraries.")
    response = input("Press [y] to continue, anything else to exit:")
    if response.strip().lower() != "y":
        exit(1)


def main():
    get_config()


if __name__ == "__main__":
    main()
