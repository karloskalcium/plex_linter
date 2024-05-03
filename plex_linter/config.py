import logging
import os
import shutil
from inspect import getsourcefile

import plexapi.exceptions
import requests
import typer
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from rich import print
from rich.prompt import Confirm
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile

from ._utils import xstr
from .non_empty_string_prompt import NonEmptyStringPrompt

# set up module logger
log = logging.getLogger(__name__)


class LinterConfig:
    # Parent dir of where this module lives
    _parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(xstr(getsourcefile(lambda: 0)))))
    config_path = os.path.join(_parent_dir, "plex_linter.toml")
    template_path = os.path.join(_parent_dir, "plex_linter.template.toml")

    def _plex_server_login(self, url: str, token: str) -> PlexServer:
        """Attempts to log into plex server, returning server if success, raises error otherwise"""
        try:
            plex = PlexServer(url, token)
        except plexapi.exceptions.Unauthorized:
            log.exception(f"Unauthorized error connecting to server {url}, check your credentials")
            raise
        except requests.exceptions.ConnectionError:
            log.exception(f"Error connecting to {url}, check the URL provided")
            raise

        return plex

    def _authenticate(self, config: TOMLDocument) -> PlexServer:
        """Gathers url, username and password from user, and repeats until successful authentication"""
        """Server URL and valid token are placed in the config when successful"""
        url = config["server"]["server_url"]
        token = config["server"]["server_token"]
        while True:
            exception_happened = True
            try:
                if (len(url) > 0) and (len(token) > 0):
                    # will throw error if login fails
                    plex = self._plex_server_login(url, token)
                    config["server"]["server_url"] = url
                    config["server"]["server_token"] = token
                    log.debug(f"Successfully logged into plex server at {url}")
                    return plex

                prompt = NonEmptyStringPrompt()
                url = prompt.ask("Plex server URL")
                user = prompt.ask("Plex username")
                password = prompt.ask("Plex password", password=True)

                account = MyPlexAccount(user, password)
                token = account.authenticationToken
            except plexapi.exceptions.Unauthorized:
                log.exception("Unauthorized error connecting to Plex, check your credentials")
                continue
            except requests.exceptions.ConnectionError:
                # error already logged in _plex_server_login method
                continue
            else:
                # from https://stackoverflow.com/a/49099889/4907881
                exception_happened = False
            finally:
                if exception_happened:
                    url = ""
                    token = ""

    def check_continue(self, config: TOMLDocument):
        """Prints out list of libraries, gives user the option to exit or continue"""
        print("Current libraries are:")
        for lib in config["content"]["libraries"]:
            print(f"  * {lib}")

        print(f"If these aren't correct, edit {LinterConfig.config_path} to add the target libraries.")
        response = Confirm.ask("Continue with these libraries?", default=True)
        if not response:
            raise typer.Exit(code=1)

    def get_plex_server(self) -> tuple[PlexServer, TOMLDocument]:
        if not os.path.exists(LinterConfig.config_path):
            shutil.copy(LinterConfig.template_path, LinterConfig.config_path)

        t = TOMLFile(LinterConfig.config_path)
        config = t.read()

        plex = self._authenticate(config)
        # write config file back out to disk
        t.write(config)

        return plex, config
