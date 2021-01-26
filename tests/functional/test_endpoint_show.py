import pytest


@pytest.mark.parametrize("ep_type", ["personal", "share", "server"])
def test_show_works(run_line, load_api_fixtures, ep_type):
    """make sure it doesn't blow up"""
    data = load_api_fixtures("endpoint_operations.yaml")
    if ep_type == "personal":
        epid = data["metadata"]["gcp_endpoint_id"]
    elif ep_type == "share":
        epid = data["metadata"]["share_id"]
    else:
        epid = data["metadata"]["endpoint_id"]

    result = run_line("globus endpoint show {}".format(epid))

    assert "Display Name:" in result.output
    assert epid in result.output


def test_show_long_description(run_line, load_api_fixtures):
    data = load_api_fixtures("endpoint_with_long_description.yaml")
    epid = data["metadata"]["endpoint_id"]

    result = run_line("globus endpoint show {}".format(epid))

    assert "Description:" in result.output
    # first few lines are there
    assert "= CLI Changelog\n" in result.output
    assert "== 1.14.0\n" in result.output
    # much later lines should have been truncated out
    assert "== 1.13.0\n" not in result.output
