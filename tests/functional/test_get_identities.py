import json


def test_default_one_id(run_line, load_api_fixtures):
    """
    Runs get-identities with one id, confirms correct username returned
    """
    data = load_api_fixtures("foo_user_info.yaml")
    user_id = data["metadata"]["user_id"]
    username = data["metadata"]["username"]
    result = run_line("globus get-identities {}".format(user_id))
    assert username + "\n" == result.output


def test_defualt_one_username(run_line, load_api_fixtures):
    """
    Runs get-identities with one username, confirms correct id returned
    """
    data = load_api_fixtures("foo_user_info.yaml")
    user_id = data["metadata"]["user_id"]
    username = data["metadata"]["username"]
    result = run_line("globus get-identities " + username)
    assert user_id + "\n" == result.output


def test_default_nosuchidentity(run_line, register_api_route):
    """
    Runs get-identities with one username, confirms correct id returned
    """
    register_api_route("auth", "/v2/api/identities", json={"identities": []})
    result = run_line("globus get-identities invalid@nosuchdomain.exists")
    assert "NO_SUCH_IDENTITY\n" == result.output


def test_invalid_username(run_line, register_api_route):
    # check that 'invalid' is called out as not being a valid username or identity
    result = run_line("globus get-identities invalid", assert_exit_code=2)
    assert "'invalid' does not appear to be a valid identity" in result.stderr


def test_default_multiple_inputs(run_line, load_api_fixtures):
    """
    Runs get-identities with id username, duplicate and invalid inputs
    Confirms order is preserved and all values are as expected
    """
    data = load_api_fixtures("multiuser_get_identities.yaml")
    users = data["metadata"]["users"]
    in_vals = [
        users[0]["username"],
        users[0]["user_id"],
        "invalid@nosuchdomain.exists",
        users[1]["username"],
        users[1]["username"],
    ]

    expected = [
        users[0]["user_id"],
        users[0]["username"],
        "NO_SUCH_IDENTITY",
        users[1]["user_id"],
        users[1]["user_id"],
    ]

    result = run_line("globus get-identities " + " ".join(in_vals))
    assert "\n".join(expected) + "\n" == result.output


def test_verbose(run_line, load_api_fixtures):
    """
    Runs get-identities with --verbose, confirms expected fields found
    """
    data = load_api_fixtures("foo_user_info.yaml")
    user_id = data["metadata"]["user_id"]
    result = run_line("globus get-identities --verbose " + user_id)
    for key in ["username", "user_id", "name", "organization", "email"]:
        assert data["metadata"][key] in result.output


def test_json(run_line, load_api_fixtures):
    """
    Runs get-identities with -F json confirms expected values
    """
    data = load_api_fixtures("foo_user_info.yaml")
    user_id = data["metadata"]["user_id"]
    output = json.loads(run_line("globus get-identities -F json " + user_id).output)
    assert data["metadata"]["user_id"] == output["identities"][0]["id"]
    for key in ["username", "name", "organization", "email"]:
        assert data["metadata"][key] == output["identities"][0][key]
