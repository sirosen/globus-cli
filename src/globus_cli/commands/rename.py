import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.services.transfer import autoactivate, get_client
from globus_cli.termio import FORMAT_TEXT_RAW, formatted_print


@command(
    "rename",
    short_help="Rename a file or directory on an endpoint",
    adoc_examples="""Rename a directory:

[source,bash]
----
$ ep_id=ddb59aef-6d04-11e5-ba46-22000b92c6ec
$ globus rename $ep_id:~/tempdir $ep_id:~/project-foo
----
""",
)
@endpoint_id_arg
@click.argument("source", metavar="SOURCE_PATH")
@click.argument("destination", metavar="DEST_PATH")
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def rename_command(endpoint_id, source, destination):
    """Rename a file or directory on an endpoint.

    The old path must be an existing file or directory. The new path must not yet
    exist.

    The new path does not have to be in the same directory as the old path, but
    most endpoints will require it to stay on the same filesystem.
    """
    client = get_client()
    autoactivate(client, endpoint_id, if_expires_in=60)

    res = client.operation_rename(endpoint_id, oldpath=source, newpath=destination)
    formatted_print(res, text_format=FORMAT_TEXT_RAW, response_key="message")
