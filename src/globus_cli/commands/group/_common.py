from __future__ import annotations

import typing as t

import click

from globus_cli.termio import Field, formatters

C = t.TypeVar("C", bound=t.Union[click.Command, t.Callable])

# cannot do this because it causes immediate imports and ruins the lazy import
# performance gain
#
# MEMBERSHIP_FIELDS = {x.value for x in globus_sdk.GroupRequiredSignupFields}
MEMBERSHIP_FIELDS = {
    "institution",
    "current_project_name",
    "address",
    "city",
    "state",
    "country",
    "address1",
    "address2",
    "zip",
    "phone",
    "department",
    "field_of_science",
}


SESSION_ENFORCEMENT_FIELD = Field(
    "Session Enforcement",
    "enforce_session",
    formatter=formatters.FuzzyBoolFormatter(true_str="strict", false_str="not strict"),
)


def _requires_subscription_id(data: dict[str, t.Any]) -> bool:
    return data.get("subscription_id") is not None


SUBSCRIPTION_FIELDS = [
    Field(
        "Subscription ID",
        "subscription_id",
        conditional=_requires_subscription_id,
    ),
    Field(
        "BAA",
        "subscription_info.is_baa",
        conditional=_requires_subscription_id,
        formatter=formatters.Bool,
    ),
    Field(
        "High Assurance",
        "subscription_info.is_high_assurance",
        conditional=_requires_subscription_id,
        formatter=formatters.Bool,
    ),
]

# fields for display of groups with and without a subscription
GROUP_FIELDS = (
    [Field("Group ID", "id")]
    + SUBSCRIPTION_FIELDS
    + [
        Field("Name", "name"),
        Field("Description", "description", wrap_enabled=True),
        Field("Type", "group_type"),
        Field("Visibility", "policies.group_visibility"),
        Field("Membership Visibility", "policies.group_members_visibility"),
        SESSION_ENFORCEMENT_FIELD,
        Field("Join Requests Allowed", "policies.join_requests"),
        Field(
            "Signup Fields",
            "policies.signup_fields",
            formatter=formatters.SortedArray,
        ),
        Field(
            "Roles",
            "my_memberships[].role",
            formatter=formatters.SortedArray,
        ),
    ]
)


def group_id_arg(f: C) -> C:
    return click.argument("GROUP_ID", type=click.UUID)(f)
