import importlib.resources
import logging
import os
import shutil

import plexapi.exceptions
import requests
import typer
from plexapi.myplex import MyPlexAccount
from plexapi.server import PlexServer
from rich import print
from rich.prompt import Confirm
from tomlkit.toml_document import TOMLDocument
from tomlkit.toml_file import TOMLFile

from .non_empty_string_prompt import NonEmptyStringPrompt

# set up module logger
log = logging.getLogger(__name__)


class LinterConfig:
    _config_dir = os.path.join(os.path.expanduser("~"), ".plex_linter")
    config_path = os.path.join(_config_dir, "plex_linter.toml")

    def _authenticate(self, config: TOMLDocument) -> PlexServer:
        """Gathers url, username and password from user, and repeats until successful authentication.
        Server URL and valid token are placed in the config when successful."""
        url = config["server"]["server_url"]
        token = config["server"]["server_token"]

        if url and token:
            try:
                plex = PlexServer(url, token)
                log.info(f"Successfully logged into plex server at {url}")
                return plex
            except plexapi.exceptions.Unauthorized, requests.exceptions.ConnectionError:
                log.exception("Saved credentials failed, prompting for new ones")

        while True:
            try:
                url = NonEmptyStringPrompt.ask("Plex server URL")
                user = NonEmptyStringPrompt.ask("Plex username")
                password = NonEmptyStringPrompt.ask("Plex password", password=True)

                account = MyPlexAccount(user, password)
                token = account.authenticationToken

                plex = PlexServer(url, token)
            except plexapi.exceptions.Unauthorized:
                log.exception("Unauthorized error connecting to Plex, check your credentials")
                continue
            except requests.exceptions.ConnectionError:
                log.exception("Connection error, check the URL provided")
                continue

            log.info(f"Successfully logged into plex server at {url}")
            config["server"]["server_url"] = url
            config["server"]["server_token"] = token
            return plex

    def check_continue(self, config: TOMLDocument):
        """Prints out list of libraries, gives user the option to exit or continue"""
        print("Current libraries are:")
        for lib in config["content"]["libraries"]:  # type: ignore[reportGeneralTypeIssues]
            print(f"  * {lib}")

        print(f"If these aren't correct, edit {LinterConfig.config_path} to add the target libraries.")
        response = Confirm.ask("Continue with these libraries?", default=True)
        if not response:
            raise typer.Exit(code=1)

    def get_plex_server(self) -> tuple[PlexServer, TOMLDocument]:
        os.makedirs(self._config_dir, exist_ok=True)
        if not os.path.exists(self.config_path):
            template = importlib.resources.files("plex_linter").joinpath("plex_linter.template.toml")
            shutil.copy(str(template), self.config_path)

        t = TOMLFile(LinterConfig.config_path)
        config = t.read()

        plex = self._authenticate(config)
        # write config file back out to disk
        t.write(config)

        return plex, config
