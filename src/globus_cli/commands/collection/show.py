from __future__ import annotations

import click

from globus_cli.login_manager import LoginManager
from globus_cli.parsing import collection_id_arg, command
from globus_cli.principal_resolver import default_identity_id_resolver
from globus_cli.termio import FORMAT_TEXT_RECORD, Field, formatted_print
from globus_cli.utils import filter_fields, sorted_json_field


def _get_standard_fields() -> list[Field]:
    from globus_cli.services.gcs import connector_id_to_display_name

    return [
        Field("Display Name"),
        Field("Owner", default_identity_id_resolver.field),
        Field("ID"),
        Field("Collection Type"),
        Field("Storage Gateway ID"),
        Field("Connector", lambda x: connector_id_to_display_name(x["connector_id"])),
        Field("Allow Guest Collections"),
        Field("Disable Anonymous Writes"),
        Field("High Assurance"),
        Field("Authentication Timeout", "authentication_timeout_mins"),
        Field("Multi-factor Authentication", "require_mfa"),
        Field("Manager URL"),
        Field("HTTPS URL"),
        Field("TLSFTP URL"),
        Field("Force Encryption"),
        Field("Public"),
        Field("Organization"),
        Field("Department"),
        Field("Keywords"),
        Field("Description"),
        Field("Contact E-mail", "contact_email"),
        Field("Contact Info"),
        Field("Collection Info Link", "info_link"),
    ]


PRIVATE_FIELDS: list[Field] = [
    Field("Root Path"),
    Field("Default Directory"),
    Field("Sharing Path Restrictions", sorted_json_field("sharing_restrict_paths")),
    Field("Sharing Allowed Users", "sharing_users_allow"),
    Field("Sharing Denied Users", "sharing_users_deny"),
    Field("Sharing Allowed POSIX Groups", "policies.sharing_groups_allow"),
    Field("Sharing Denied POSIX Groups", "policies.sharing_groups_deny"),
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
@LoginManager.requires_login(LoginManager.TRANSFER_RS, LoginManager.AUTH_RS)
def collection_show(
    *, login_manager: LoginManager, include_private_policies, collection_id
):
    """
    Display a Mapped or Guest Collection
    """
    gcs_client = login_manager.get_gcs_client(collection_id=collection_id)

    query_params = {}
    fields = _get_standard_fields()

    if include_private_policies:
        query_params["include"] = "private_policies"
        fields += PRIVATE_FIELDS

    res = gcs_client.get_collection(collection_id, query_params=query_params)

    # walk the list of all known fields and reduce the rendering to only look
    # for fields which are actually present
    real_fields = filter_fields(fields, res)

    formatted_print(
        res,
        text_format=FORMAT_TEXT_RECORD,
        fields=real_fields,
    )
