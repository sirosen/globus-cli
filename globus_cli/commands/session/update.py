import uuid

import click

from globus_cli.helpers import (
    do_link_auth_flow,
    do_local_server_auth_flow,
    is_remote_session,
)
from globus_cli.parsing import common_options, no_local_server_option
from globus_cli.safeio import safeprint
from globus_cli.services.auth import get_auth_client


@click.command(
    "update",
    short_help=("Update your CLI auth session"),
    help=(
        "Update your current CLI auth session by authenticating "
        "with specific identities."
    ),
)
@common_options(no_format_option=True, no_map_http_status_option=True)
@no_local_server_option
@click.argument("identities", nargs=-1, required=False)
@click.option(
    "--all", is_flag=True, help="authenticate with every identity in your identity set"
)
def session_update(identities, no_local_server, all):

    if (not (identities or all)) or (identities and all):
        raise click.UsageError("Either give one or more IDENTITIES or use --all")
    auth_client = get_auth_client()

    # if --all use every identity id in the user's identity set
    if all:
        res = auth_client.oauth2_userinfo()
        try:
            identity_ids = [user["sub"] for user in res["identity_set"]]
        except KeyError:
            safeprint(
                "Your current login does not have the consents required "
                "to view your full identity set. Please log in again "
                "to agree to the required consents.",
                write_to_stderr=True,
            )
            click.get_current_context().exit(1)

    # otherwise try to resolve any non uuid values to identity ids
    else:
        identity_ids = []
        identity_names = []

        for val in identities:
            try:
                uuid.UUID(val)
                identity_ids.append(val)
            except ValueError:
                identity_names.append(val)

        if identity_names:
            res = auth_client.get_identities(usernames=identity_names)["identities"]

            for name in identity_names:
                for identity in res:
                    if identity["username"] == name:
                        identity_ids.append(identity["id"])
                        break
                else:
                    safeprint("No such identity {}".format(val), write_to_stderr=True)
                    click.get_current_context().exit(1)

    # create session params once we have all identity ids
    session_params = {
        "session_required_identities": ",".join(identity_ids),
        "session_message": "Authenticate to update your CLI session.",
    }

    # use a link login if remote session or user requested
    if no_local_server or is_remote_session():
        do_link_auth_flow(session_params=session_params)

    # otherwise default to a local server login flow
    else:
        safeprint(
            "You are running 'globus session update', "
            "which should automatically open a browser window for you to "
            "authenticate with specific identities.\n"
            "If this fails or you experience difficulty, try "
            "'globus session update --no-local-server'"
            "\n---"
        )
        do_local_server_auth_flow(session_params=session_params)

    safeprint(
        "\nYou have successfully updated your CLI session.\n"
        "Use 'globus session show' to see the updated session."
    )
