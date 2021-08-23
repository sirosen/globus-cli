import uuid

import pytest

from globus_cli.services.transfer import EndpointType


@pytest.mark.parametrize(
    "doc,expected",
    [
        ({}, EndpointType.NON_GCSV5_ENDPOINT),
        ({"is_globus_connect": True}, EndpointType.GCP),
        ({"non_functional": True}, EndpointType.GCSV5_ENDPOINT),
        ({"host_endpoint_id": str(uuid.uuid4())}, EndpointType.SHARE),
        ({"gcs_version": "5.4.1"}, EndpointType.MAPPED_COLLECTION),
        (
            {"gcs_version": "5.4.1", "host_endpoint_id": str(uuid.uuid4())},
            EndpointType.GUEST_COLLECTION,
        ),
    ],
)
def test_determine_endpoint_type(doc, expected):
    assert EndpointType.determine_endpoint_type(doc) == expected
