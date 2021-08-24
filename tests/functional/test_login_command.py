from unittest import mock

import globus_sdk

from globus_cli.login_manager import LoginManager


def test_login_validates_token(run_line, mock_login_token_response):
    # turn off test mode, to allow token validation
    LoginManager._TEST_MODE = False

    with mock.patch("globus_cli.login_manager.manager.internal_auth_client") as m:
        ac = mock.MagicMock(spec=globus_sdk.NativeAppAuthClient)
        m.return_value = ac

        run_line("globus login")

        by_rs = mock_login_token_response.by_resource_server
        a_rt = by_rs["auth.globus.org"]["refresh_token"]
        t_rt = by_rs["transfer.api.globus.org"]["refresh_token"]
        ac.oauth2_validate_token.assert_any_call(a_rt)
        ac.oauth2_validate_token.assert_any_call(t_rt)
