import click

from globus_cli.endpointish import Endpointish
from globus_cli.login_manager import LoginManager
from globus_cli.parsing import command, endpoint_id_arg
from globus_cli.termio import FORMAT_TEXT_RECORD, Field, formatted_print

STANDARD_FIELDS = (
    Field("Display Name"),
    Field("ID"),
    Field("Owner", "owner_string"),
    Field("Description", wrap_enabled=True),
    Field("Activated"),
    Field("Shareable"),
    Field("Department"),
    Field("Keywords"),
    Field("Endpoint Info Link", "info_link"),
    Field("Contact E-mail", "contact_email"),
    Field("Organization"),
    Field("Department"),
    Field("Other Contact Info", "contact_info"),
    Field("Visibility", "public"),
    Field("Default Directory"),
    Field("Force Encryption"),
    Field("Managed Endpoint", "subscription_id", typ=Field.types.Bool),
    Field("Subscription ID"),
    Field("Legacy Name", "canonical_name"),
    Field("Local User Info Available"),
)

GCP_FIELDS = STANDARD_FIELDS + (
    Field("GCP Connected"),
    Field("GCP Paused (macOS only)", "gcp_paused"),
)


@command("show")
@endpoint_id_arg
@click.option("--skip-endpoint-type-check", is_flag=True, hidden=True)
@LoginManager.requires_login(LoginManager.TRANSFER_RS)
def endpoint_show(
    *, login_manager: LoginManager, endpoint_id: str, skip_endpoint_type_check: bool
) -> None:
    """Display a detailed endpoint definition"""
    transfer_client = login_manager.get_transfer_client()
    if not skip_endpoint_type_check:
        Endpointish(
            endpoint_id, transfer_client=transfer_client
        ).assert_is_not_collection()

    res = transfer_client.get_endpoint(endpoint_id)

    formatted_print(
        res,
        text_format=FORMAT_TEXT_RECORD,
        fields=GCP_FIELDS if res["is_globus_connect"] else STANDARD_FIELDS,
    )
