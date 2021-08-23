from enum import Enum, auto


class EndpointType(Enum):
    # endpoint / collection types
    GCP = auto()
    GCSV5_ENDPOINT = auto()
    GUEST_COLLECTION = auto()
    MAPPED_COLLECTION = auto()
    SHARE = auto()
    NON_GCSV5_ENDPOINT = auto()  # most likely GCSv4, but not necessarily

    @classmethod
    def determine_endpoint_type(cls, ep_doc: dict) -> "EndpointType":
        """
        Given an endpoint document from transfer, determine what type of
        endpoint or collection it is for
        """
        if ep_doc.get("is_globus_connect") is True:
            return EndpointType.GCP

        if ep_doc.get("non_functional") is True:
            return EndpointType.GCSV5_ENDPOINT

        shared = ep_doc.get("host_endpoint_id") is not None

        if ep_doc.get("gcs_version"):
            major, minor, patch = ep_doc["gcs_version"].split(".")
            gcsv5 = major == "5"
        else:
            gcsv5 = False

        if gcsv5:
            if shared:
                return EndpointType.GUEST_COLLECTION
            else:
                return EndpointType.MAPPED_COLLECTION

        elif shared:
            return EndpointType.SHARE

        return EndpointType.NON_GCSV5_ENDPOINT
