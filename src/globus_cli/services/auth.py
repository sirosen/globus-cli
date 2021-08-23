import uuid

from globus_sdk import AuthClient, RefreshTokenAuthorizer

from globus_cli import version
from globus_cli.login_manager import internal_auth_client, token_storage_adapter

# what qualifies as a valid Identity Name?
_IDENTITY_NAME_REGEX = r"^[a-zA-Z0-9]+.*@[a-zA-z0-9-]+\..*[a-zA-Z]+$"

# constant for token and login management
AUTH_RESOURCE_SERVER = "auth.globus.org"


def _is_uuid(s):
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


def get_auth_client():
    adapter = token_storage_adapter()
    tokens = adapter.get_token_data("auth.globus.org")
    authorizer = None

    # if there are tokens, build the authorizer
    if tokens is not None:
        authorizer = RefreshTokenAuthorizer(
            tokens["refresh_token"],
            internal_auth_client(),
            tokens["access_token"],
            tokens["expires_at_seconds"],
            on_refresh=adapter.on_refresh,
        )

    client = AuthClient(authorizer=authorizer, app_name=version.app_name)
    return client


def _lookup_identity_field(id_name=None, id_id=None, field="id", provision=False):
    assert (id_name or id_id) and not (id_name and id_id)
    client = get_auth_client()

    kw = dict(provision=provision)
    if id_name:
        kw.update({"usernames": id_name})
    else:
        kw.update({"ids": id_id})

    try:
        return client.get_identities(**kw)["identities"][0][field]
    except (IndexError, KeyError):
        # IndexError: identity does not exist and wasn't provisioned
        # KeyError: `field` does not exist for the requested identity
        return None


def maybe_lookup_identity_id(identity_name, provision=False):
    if _is_uuid(identity_name):
        return identity_name
    else:
        return _lookup_identity_field(id_name=identity_name, provision=provision)


def lookup_identity_name(identity_id):
    return _lookup_identity_field(id_id=identity_id, field="username")
