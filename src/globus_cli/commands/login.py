import click
from globus_sdk import AuthAPIError

from globus_cli.login_manager import (
    do_link_auth_flow,
    do_local_server_auth_flow,
    internal_auth_client,
    is_remote_session,
    token_storage_adapter,
)
from globus_cli.parsing import command, no_local_server_option

_SHARED_EPILOG = """\

You can check your primary identity with
  globus whoami

For information on which of your identities are in session use
  globus session show

Logout of the Globus CLI with
  globus logout
"""

_LOGIN_EPILOG = (
    (
        """\

You have successfully logged in to the Globus CLI!
"""
    )
    + _SHARED_EPILOG
)

_LOGGED_IN_RESPONSE = (
    (
        """\
You are already logged in!

You may force a new login with
  globus login --force
"""
    )
    + _SHARED_EPILOG
)


@command(
    "login",
    short_help="Log into Globus to get credentials for the Globus CLI",
    disable_options=["format", "map_http_status"],
)
@no_local_server_option
@click.option(
    "--force",
    is_flag=True,
    help=("Do a fresh login, ignoring any existing credentials"),
)
def login_command(no_local_server, force):
    """
    Get credentials for the Globus CLI

    Necessary before any Globus CLI commands which require authentication will work

    This command directs you to the page necessary to permit the Globus CLI to make API
    calls for you, and gets the OAuth2 tokens needed to use those permissions.

    The default login method opens your browser to the Globus CLI's authorization
    page, where you can read and consent to the permissions required to use the
    Globus CLI. The CLI then takes care of getting the credentials through a
    local server.

    If the CLI detects you are on a remote session, or the --no-local-server option is
    used, the CLI will instead print a link for you to manually follow to the Globus
    CLI's authorization page. After consenting you will then need to copy and paste the
    given access code from the web to the CLI.
    """
    # if not forcing, stop if user already logged in
    if not force and check_logged_in():
        click.echo(_LOGGED_IN_RESPONSE)
        return

    # use a link login if remote session or user requested
    if no_local_server or is_remote_session():
        do_link_auth_flow()

    # otherwise default to a local server login flow
    else:
        click.echo(
            "You are running 'globus login', which should automatically open "
            "a browser window for you to login.\n"
            "If this fails or you experience difficulty, try "
            "'globus login --no-local-server'"
            "\n---"
        )
        do_local_server_auth_flow()

    # print epilog
    click.echo(_LOGIN_EPILOG)


def check_logged_in():
    adapter = token_storage_adapter()

    # first, try to get the tokens from storage
    transfer_tkn = adapter.get_token_data("transfer.api.globus.org")
    auth_tkn = adapter.get_token_data("auth.globus.org")

    # if either of the token dicts are null return False
    if transfer_tkn is None or auth_tkn is None:
        return False

    # get the instance client
    auth_client = internal_auth_client()

    # check that refresh tokens and client are valid
    try:
        for token_data in (transfer_tkn, auth_tkn):
            token = token_data["refresh_token"]
            res = auth_client.oauth2_validate_token(token)
            if not res["active"]:
                return False
    # if the instance client is invalid, an AuthAPIError will be raised
    except AuthAPIError:
        return False

    return True
