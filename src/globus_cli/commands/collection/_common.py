from __future__ import annotations

import click
import globus_sdk

from globus_cli.login_manager.utils import get_current_identity_id
from globus_cli.termio import Field, FilteredField, formatters


class LazyCurrentIdentity:
    def __init__(self, value: str | None) -> None:
        self._value = value

    @property
    def value(self) -> str:
        if self._value is None:
            self._value = get_current_identity_id()
        return str(self._value)


def _identity_id_callback(
    ctx: click.Context | None,
    param: click.Parameter | None,
    value: str | None,
) -> LazyCurrentIdentity:
    return LazyCurrentIdentity(value)


# NB: this is implemented using a callback rather than a custom type because this lets
# us ensure that we convert the default of `None` to `LazyCurrentIdentity(None)`
# a custom type would still pass a default of `None` unless a callback were specified
identity_id_option = click.option(
    "--identity-id",
    help="User who should own the collection (defaults to the current user)",
    callback=_identity_id_callback,
)


def standard_collection_fields(auth_client: globus_sdk.AuthClient) -> list[Field]:
    from globus_cli.services.gcs import ConnectorIdFormatter

    return [
        FilteredField("Display Name", "display_name"),
        FilteredField(
            "Owner",
            "identity_id",
            formatter=formatters.auth.IdentityIDFormatter(auth_client),
        ),
        FilteredField("ID", "id"),
        FilteredField("Collection Type", "collection_type"),
        FilteredField("Mapped Collection ID", "mapped_collection_id"),
        FilteredField("User Credential ID", "user_credential_id"),
        FilteredField("Storage Gateway ID", "storage_gateway_id"),
        FilteredField("Connector", "connector_id", formatter=ConnectorIdFormatter()),
        FilteredField("Allow Guest Collections", "allow_guest_collections"),
        FilteredField("Disable Anonymous Writes", "disable_anonymous_writes"),
        FilteredField("High Assurance", "high_assurance"),
        FilteredField(
            "Authentication Timeout (Minutes)", "authentication_timeout_mins"
        ),
        FilteredField("Multi-factor Authentication", "require_mfa"),
        FilteredField("Manager URL", "manager_url"),
        FilteredField("HTTPS URL", "https_url"),
        FilteredField("TLSFTP URL", "tlsftp_url"),
        FilteredField("Force Encryption", "force_encryption"),
        FilteredField("Public", "public"),
        FilteredField("Organization", "organization"),
        FilteredField("Department", "department"),
        FilteredField("Keywords", "keywords"),
        FilteredField("Description", "description"),
        FilteredField("Contact E-mail", "contact_email"),
        FilteredField("Contact Info", "contact_info"),
        FilteredField("Collection Info Link", "info_link"),
        FilteredField("User Message", "user_message"),
        FilteredField("User Message Link", "user_message_link"),
    ]
