from __future__ import annotations

import typing as t

import globus_sdk

from globus_cli.version import __version__, app_name

if t.TYPE_CHECKING:
    C = t.TypeVar("C", bound=globus_sdk.BaseClient)


def add_cli_clientinfo(client: C) -> C:
    client.transport.globus_client_info.add(
        {"product": "globus-cli", "version": __version__}
    )
    client.app_name = app_name
