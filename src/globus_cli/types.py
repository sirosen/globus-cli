"""
Internal types for type annotations
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Mapping, Union

# all imports from globus_cli modules done here are done under TYPE_CHECKING
# in order to ensure that the use of type annotations never introduces circular
# imports at runtime
if TYPE_CHECKING:
    import globus_sdk

    from globus_cli.utils import CLIStubResponse

DATA_CONTAINER_T = Union[
    Mapping[str, Any],
    "globus_sdk.GlobusHTTPResponse",
    "CLIStubResponse",
]
