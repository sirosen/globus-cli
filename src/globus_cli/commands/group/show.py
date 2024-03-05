import uuid

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command
from globus_cli.termio import TextMode, display

from ._common import GROUP_FIELDS, group_id_arg


@group_id_arg
@command("show")
@LoginManager.requires_login("groups")
def group_show(login_manager: LoginManager, *, group_id: uuid.UUID) -> None:
    """Show a group definition"""
    groups_client = login_manager.get_groups_client()

    group = groups_client.get_group(group_id, include="my_memberships")

    display(group, text_mode=TextMode.text_record, fields=GROUP_FIELDS)
