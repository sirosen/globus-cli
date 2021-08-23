import uuid
from unittest import mock

import pytest
from globus_sdk import TransferAPIError

from globus_cli.commands.bookmark._common import resolve_id_or_name


def test_resolve_bookmarkid_not_found_does_name_match():
    err_res = mock.MagicMock()
    err_res.status_code = 404
    err_res.json.return_value = {
        "code": "BookmarkNotFound",
        "message": "foo",
        "request_id": "bar",
    }
    err_res.headers = {"Content-Type": "application/json"}

    client = mock.MagicMock()
    client.get_bookmark.side_effect = TransferAPIError(err_res)

    bookmarkid = str(uuid.uuid1())
    magic_result = {"name": bookmarkid, "_sentinel": object()}
    client.bookmark_list.return_value = [magic_result]

    res = resolve_id_or_name(client, bookmarkid)
    assert res == magic_result


@pytest.mark.parametrize("status,code", [(404, "OtherNotFound"), (500, "Generic")])
def test_resolve_bookmarkid_any_other_error_reraise(status, code):
    err_res = mock.MagicMock()
    err_res.status_code = status
    err_res.json.return_value = {"code": code, "message": "foo", "request_id": "bar"}
    err_res.headers = {"Content-Type": "application/json"}

    client = mock.MagicMock()
    client.get_bookmark.side_effect = TransferAPIError(err_res)

    bookmarkid = str(uuid.uuid1())

    with pytest.raises(TransferAPIError):
        resolve_id_or_name(client, bookmarkid)


def test_resolve_bookmark_no_match_in_list():
    bookmark_name = "foo"

    client = mock.MagicMock()
    client.bookmark_list.return_value = [{"name": "bar"}]

    with mock.patch("globus_cli.commands.bookmark._common.click") as m:
        fakectx = mock.Mock()
        fakectx.exit = mock.Mock()
        m.echo = mock.Mock()
        m.get_current_context.return_value = fakectx

        resolve_id_or_name(client, bookmark_name)

        fakectx.exit.assert_called_once_with(1)
        m.echo.assert_called_once_with('No bookmark found for "foo"', err=True)
