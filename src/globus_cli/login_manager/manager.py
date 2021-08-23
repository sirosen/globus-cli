import functools

import click

from globus_cli.utils import format_list_of_words, format_plural_str

from .tokenstore import token_storage_adapter


class LoginManager:
    def __init__(self):
        self._token_storage = token_storage_adapter()

    def has_login(self, resource_server: str):
        """
        Determines if the user has a refresh token for the given
        resource server
        """
        tokens = self._token_storage.get_token_data(resource_server)
        return tokens is not None and "refresh_token" in tokens


def requires_login(*resource_servers: str, pass_manager: bool = False):
    """
    Command decorator for specifying a resource server that the user must have
    tokens for in order to run the command.

    Simple usage for commands that have static resource needs: simply list all
    needed resource servers as args:

    @requries_login("auth.globus.org")

    @requires_login("auth.globus.org", "transfer.api.globus.org")

    Usage for commands which have dynamic resource servers depending
    on the arguments passed to the command (e.g. commands for the GCS API)

    @requies_login(pass_manager=True)
    def command(login_manager, endpoint_id)

        login_manager.<do the thing>(endpoint_id)

    """

    def inner(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            manager = LoginManager()

            # determine the set of resource servers missing logins
            missing_servers = {s for s in resource_servers if not manager.has_login(s)}

            # if we are missing logins, assemble error text
            # text is slightly different for 1, 2, or 3+ missing servers
            if missing_servers:
                server_string = format_list_of_words(*missing_servers)
                message_prefix = format_plural_str(
                    "Missing {login}", {"login": "logins"}, len(missing_servers) != 1
                )

                raise click.ClickException(
                    message_prefix + f" for {server_string}, please run 'globus login'"
                )

            # if pass_manager is True, pass it as an additional positional arg
            if pass_manager:
                return func(*args, manager, **kwargs)
            else:
                return func(*args, **kwargs)

        return wrapper

    return inner
