import logging
import os
import shlex
import time
import urllib.parse
from unittest import mock

import globus_sdk
import pytest
import responses
from click.testing import CliRunner
from globus_sdk.tokenstorage import SQLiteAdapter
from globus_sdk.transport import RequestsTransport
from globus_sdk.utils import slash_join
from ruamel.yaml import YAML

import globus_cli

yaml = YAML()
log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def go_ep1_id():
    return "ddb59aef-6d04-11e5-ba46-22000b92c6ec"


@pytest.fixture(scope="session")
def go_ep2_id():
    return "ddb59af0-6d04-11e5-ba46-22000b92c6ec"


@pytest.fixture(scope="session")
def task_id():
    return "549ef13c-600f-11eb-9608-0afa7b051b85"


@pytest.fixture
def mock_login_token_response():
    mock_token_res = mock.Mock()
    mock_token_res.by_resource_server = {
        "auth.globus.org": {
            "scope": "openid profile email "
            "urn:globus:auth:scope:auth.globus.org:view_identity_set",
            "refresh_token": "AuthRT",
            "access_token": "AuthAT",
            "token_type": "bearer",
            "expires_at_seconds": int(time.time()) + 120,
            "resource_server": "auth.globus.org",
        },
        "transfer.api.globus.org": {
            "scope": "urn:globus:auth:scope:transfer.api.globus.org:all",
            "refresh_token": "TransferRT",
            "access_token": "TransferAT",
            "token_type": "bearer",
            "expires_at_seconds": int(time.time()) + 120,
            "resource_server": "transfer.api.globus.org",
        },
    }
    return mock_token_res


@pytest.fixture
def test_token_storage(mock_login_token_response):
    """Put memory-backed sqlite token storage in place for the testsuite to use."""
    mockstore = SQLiteAdapter(":memory:")
    mockstore.store_config(
        "auth_client_data",
        {"client_id": "fakeClientIDString", "client_secret": "fakeClientSecret"},
    )
    mockstore.store(mock_login_token_response)
    return mockstore


@pytest.fixture(autouse=True)
def patch_tokenstorage(monkeypatch, test_token_storage):
    monkeypatch.setattr(
        globus_cli.login_manager.token_storage_adapter,
        "_instance",
        test_token_storage,
        raising=False,
    )


@pytest.fixture(scope="session")
def test_file_dir():
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "files"))


@pytest.fixture
def cli_runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture
def run_line(cli_runner, request, patch_tokenstorage):
    """
    Uses the CliRunner to run the given command line.

    Asserts that the exit_code is equal to the given assert_exit_code,
    and if that exit_code is 0 prevents click from catching exceptions
    for easier debugging.
    """

    def func(line, assert_exit_code=0, stdin=None):
        from globus_cli import main

        # split line into args and confirm line starts with "globus"
        args = shlex.split(line)
        assert args[0] == "globus"

        # run the line. globus_cli.main is the "globus" part of the line
        # if we are expecting success (0), don't catch any exceptions.
        result = cli_runner.invoke(
            main, args[1:], input=stdin, catch_exceptions=bool(assert_exit_code)
        )
        if result.exit_code != assert_exit_code:
            raise (
                Exception(
                    (
                        "CliTest run_line exit_code assertion failed!\n"
                        "Line:\n{}\nexited with {} when expecting {}\n"
                        "stdout:\n{}\nstderr:\n{}\nnetwork calls recorded:"
                        "\n  {}"
                    ).format(
                        line,
                        result.exit_code,
                        assert_exit_code,
                        result.stdout,
                        result.stderr,
                        (
                            "\n  ".join(
                                f"{r.request.method} {r.request.url}"
                                for r in responses.calls
                            )
                            or "  <none>"
                        ),
                    )
                )
            )
        return result

    return func


@pytest.fixture(autouse=True)
def mocked_responses(monkeypatch):
    """
    All tests enable `responses` patching of the `requests` package, replacing
    all HTTP calls.
    """
    responses.start()

    # while request mocking is running, ensure GLOBUS_SDK_ENVIRONMENT is set to
    # production
    monkeypatch.setitem(os.environ, "GLOBUS_SDK_ENVIRONMENT", "production")

    yield

    responses.stop()
    responses.reset()


@pytest.fixture
def register_api_route(mocked_responses):
    # copied almost verbatim from the SDK testsuite
    def func(
        service,
        path,
        method=responses.GET,
        adding_headers=None,
        replace=False,
        match_querystring=False,
        **kwargs,
    ):
        base_url_map = {
            "auth": "https://auth.globus.org/",
            "nexus": "https://nexus.api.globusonline.org/",
            "transfer": "https://transfer.api.globus.org/v0.10",
            "search": "https://search.api.globus.org/",
        }
        assert service in base_url_map
        base_url = base_url_map.get(service)
        full_url = slash_join(base_url, path)

        # can set it to `{}` explicitly to clear the default
        if adding_headers is None:
            adding_headers = {"Content-Type": "application/json"}

        if replace:
            responses.replace(
                method,
                full_url,
                headers=adding_headers,
                match_querystring=match_querystring,
                **kwargs,
            )
        else:
            responses.add(
                method,
                full_url,
                headers=adding_headers,
                match_querystring=match_querystring,
                **kwargs,
            )

    return func


def _iter_fixture_routes(routes):
    # walk a fixture file either as a list of routes
    for x in routes:
        # copy and remove elements
        params = dict(x)
        path = params.pop("path")
        method = params.pop("method", "get")
        yield path, method, params


@pytest.fixture
def load_api_fixtures(register_api_route, test_file_dir, go_ep1_id, go_ep2_id, task_id):
    def func(filename):
        filename = os.path.join(test_file_dir, "api_fixtures", filename)
        with open(filename) as fp:
            data = yaml.load(fp.read())
        for service, routes in data.items():
            # allow use of the key "metadata" to expose extra data from a fixture file
            # to the user of it
            if service == "metadata":
                continue

            for path, method, params in _iter_fixture_routes(routes):
                # allow /endpoint/{GO_EP1_ID} as a path
                use_path = path.format(
                    GO_EP1_ID=go_ep1_id, GO_EP2_ID=go_ep2_id, TASK_ID=task_id
                )
                if "query_params" in params:
                    # copy and set match_querystring=True
                    params = dict(match_querystring=True, **params)
                    # remove and encode query params
                    query_params = urllib.parse.urlencode(params.pop("query_params"))
                    # modify path (assume no prior params)
                    use_path = use_path + "?" + query_params
                print(
                    f"debug: register_api_route({service}, {use_path}, {method}, ...)"
                )
                register_api_route(service, use_path, method=method.upper(), **params)

        # after registration, return the raw fixture data
        return data

    return func


@pytest.fixture(autouse=True)
def disable_client_retries(monkeypatch):
    class NoRetryTransport(RequestsTransport):
        DEFAULT_MAX_RETRIES = 0

    monkeypatch.setattr(globus_sdk.TransferClient, "transport_class", NoRetryTransport)
    monkeypatch.setattr(globus_sdk.AuthClient, "transport_class", NoRetryTransport)
    monkeypatch.setattr(
        globus_sdk.NativeAppAuthClient, "transport_class", NoRetryTransport
    )
    monkeypatch.setattr(
        globus_sdk.ConfidentialAppAuthClient, "transport_class", NoRetryTransport
    )
