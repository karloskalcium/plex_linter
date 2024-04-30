import logging
import os
import shutil
from inspect import getsourcefile
from pprint import pformat

import plexapi.exceptions
import requests
import typer
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from rich.prompt import Confirm
from tomlkit import toml_file

from .non_empty_string_prompt import NonEmptyStringPrompt

# Get the path of where this module lives
config_path = os.path.join(os.path.dirname(os.path.abspath(getsourcefile(lambda: 0))), "../plex_linter.config.toml")
template_path = os.path.join(
    os.path.dirname(os.path.abspath(getsourcefile(lambda: 0))), "../plex_linter.config.template.toml"
)


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
    """Server URL and valid token are placed in the config when successful"""
    url = config["server"]["server_url"]
    token = config["server"]["server_token"]
    while True:
        exception_happened = True
        try:
            if (len(url) > 0) and (len(token) > 0):
                # will throw error if login fails
                plex = plex_server_login(url, token)
                config["server"]["server_url"] = url
                config["server"]["server_token"] = token
                return plex

            prompt = NonEmptyStringPrompt()
            url = prompt.ask("Plex server URL")
            user = prompt.ask("Plex username")
            password = prompt.ask("Plex password", password=True)

            account = MyPlexAccount(user, password)
            token = account.authenticationToken
        except plexapi.exceptions.Unauthorized:
            logging.error("Unauthorized error connecting to Plex, check your credentials")
            continue
        except requests.exceptions.ConnectionError:
            # error already logged in plex_server_login method
            continue
        else:
            # from https://stackoverflow.com/a/49099889/4907881
            exception_happened = False
        finally:
            if exception_happened:
                url = ""
                token = ""


def get_config() -> PlexServer:
    if not os.path.exists(config_path):
        shutil.copy(template_path, config_path)

    t = toml_file.TOMLFile(config_path)
    config = t.read()
    logging.debug(pformat(config))

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
    response = Confirm.ask("Continue with these libraries?", default=True)
    if not response:
        exit(1)


def main():
    get_config()


if __name__ == "__main__":
    main()
