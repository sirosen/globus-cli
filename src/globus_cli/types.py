"""
Internal types for type annotations
"""

from __future__ import annotations

import typing as t

import click

# all imports from globus_cli modules done here are done under TYPE_CHECKING
# in order to ensure that the use of type annotations never introduces circular
# imports at runtime
if t.TYPE_CHECKING:
    import globus_sdk


AnyCallable: t.TypeAlias = t.Callable[..., t.Any]
AnyCommand: t.TypeAlias = t.Union[click.Command, AnyCallable]


ClickContextTree: t.TypeAlias = t.Tuple[
    click.Context, t.List[click.Context], t.List["ClickContextTree"]
]


DATA_CONTAINER_T: t.TypeAlias = t.Union[
    t.Mapping[str, t.Any],
    "globus_sdk.GlobusHTTPResponse",
]

JsonValue: t.TypeAlias = t.Union[
    int, float, str, bool, None, t.List["JsonValue"], t.Dict[str, "JsonValue"]
]


ServiceNameLiteral: t.TypeAlias = t.Literal[
    "auth", "transfer", "groups", "search", "timers", "flows"
]
