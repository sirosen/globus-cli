import uuid

from globus_cli.parsing import EXPLICIT_NULL


def display_name_or_cname(ep_doc):
    return ep_doc["display_name"] or ep_doc["canonical_name"]


def iterable_response_to_dict(iterator):
    output_dict = {"DATA": []}
    for item in iterator:
        dat = item
        try:
            dat = item.data
        except AttributeError:
            pass
        output_dict["DATA"].append(dat)
    return output_dict


def assemble_generic_doc(datatype, **kwargs):
    doc = {"DATA_TYPE": datatype}
    for key, val in kwargs.items():
        if isinstance(val, uuid.UUID):
            val = str(val)

        if val == EXPLICIT_NULL:
            doc[key] = None
        elif val is not None:
            doc[key] = val
    return doc
