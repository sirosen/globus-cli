from __future__ import annotations

import uuid

import click

from globus_cli.commands.collection._common import standard_collection_fields
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command
from globus_cli.termio import Field, FilteredField, TextMode, display, formatters

PRIVATE_FIELDS: list[Field] = [
    FilteredField("Root Path", "root_path"),
    FilteredField("Default Directory", "default_directory"),
    FilteredField(
        "Sharing Path Restrictions",
        "sharing_restrict_paths",
        formatter=formatters.SortedJson,
    ),
    FilteredField("Sharing Allowed Users", "sharing_users_allow"),
    FilteredField("Sharing Denied Users", "sharing_users_deny"),
    FilteredField("Sharing Allowed POSIX Groups", "policies.sharing_groups_allow"),
    FilteredField("Sharing Denied POSIX Groups", "policies.sharing_groups_deny"),
]


@command("show", short_help="Show a Collection definition")
@collection_id_arg
@click.option(
    "--include-private-policies",
    is_flag=True,
    help=(
        "Include private policies. Requires administrator role on the endpoint. "
        "Some policy data may only be visible in `--format JSON` output"
    ),
)
@LoginManager.requires_login("auth", "transfer")
def collection_show(
    login_manager: LoginManager,
    *,
    include_private_policies: bool,
    collection_id: uuid.UUID,
) -> None:
    """
    Display a Mapped or Guest Collection
    """
    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)

    query_params = {}
    fields: list[Field] = standard_collection_fields(login_manager.get_auth_client())

    if include_private_policies:
        query_params["include"] = "private_policies"
        fields += PRIVATE_FIELDS

    res = gcs_client.get_collection(collection_id, query_params=query_params)

    display(res, text_mode=TextMode.text_record, fields=fields)
