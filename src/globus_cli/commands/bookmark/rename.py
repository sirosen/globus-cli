import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.services.transfer import get_client
from globus_cli.termio import formatted_print

from ._common import resolve_id_or_name


@command(
    "rename",
    adoc_output=(
        "When textual output is requested, the only output on a successful rename "
        "is a success message."
    ),
    adoc_examples="""
Rename a bookmark named "oldname" to "newname":

[source,bash]
----
$ globus bookmark rename oldname newname
----
""",
)
@click.argument("bookmark_id_or_name")
@click.argument("new_bookmark_name")
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def bookmark_rename(bookmark_id_or_name, new_bookmark_name):
    """Change a bookmark's name"""
    client = get_client()
    bookmark_id = resolve_id_or_name(client, bookmark_id_or_name)["id"]

    submit_data = {"name": new_bookmark_name}

    res = client.update_bookmark(bookmark_id, submit_data)
    formatted_print(res, simple_text="Success")
