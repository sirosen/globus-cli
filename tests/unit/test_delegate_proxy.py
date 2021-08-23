import os

import pytest

from globus_cli.services.transfer import fill_delegate_proxy_activation_requirements


@pytest.fixture
def pubkey(test_file_dir):
    with open(os.path.join(test_file_dir, "pubkey.pem")) as f:
        return f.read()


def test_fill_delegate_proxy_activation_requirements(pubkey):
    """
    Uses the public key from fixtures to form a fake activation
    requirements response, and an expired proxy to test
    fill_delegate_proxy_activation_requirements.
    """
    # file containing an expired x509 from a myproxy-logon
    x509 = "tests/files/cert.pem"

    activation_requirements = {
        "DATA_TYPE": "activation_requirements",
        "DATA": [
            {
                "DATA_TYPE": "activation_requirement",
                "type": "delegate_proxy",
                "name": "public_key",
                "value": pubkey,
            },
            {
                "DATA_TYPE": "activation_requirement",
                "type": "delegate_proxy",
                "name": "proxy_chain",
                "value": None,
            },
        ],
    }

    filled_requirements = fill_delegate_proxy_activation_requirements(
        activation_requirements, x509
    )

    # assert the proxy_chain now contains a certificate
    assert "-----BEGIN CERTIFICATE-----" in filled_requirements["DATA"][1]["value"]
    assert "-----END CERTIFICATE-----" in filled_requirements["DATA"][1]["value"]


@pytest.mark.parametrize(
    "errty,errmatch,inputfile",
    [
        (IOError, "No such file", "nosuchfile.pem"),
        (ValueError, "Unable to parse PEM data", "tests/conftest.py"),
        (ValueError, "Unable to parse PEM data", "tests/files/no_cert.pem"),
        (ValueError, "Failed to decode PEM data", "tests/files/no_key.pem"),
    ],
)
def test_bad_x509(pubkey, errty, errmatch, inputfile):
    """
    Uses the public key from fixtures to form a fake activation
    requirements response, then attempts to fill the activation
    requirements with bad x509 files. Confirms value errors
    """
    activation_requirements = {
        "DATA_TYPE": "activation_requirements",
        "DATA": [
            {
                "DATA_TYPE": "activation_requirement",
                "type": "delegate_proxy",
                "name": "public_key",
                "value": pubkey,
            },
            {
                "DATA_TYPE": "activation_requirement",
                "type": "delegate_proxy",
                "name": "proxy_chain",
                "value": None,
            },
        ],
    }

    with pytest.raises(errty, match=errmatch):
        fill_delegate_proxy_activation_requirements(activation_requirements, inputfile)
