"""
Setup a custom except hook which formats exceptions that are uncaught.
In "DEBUGMODE", we'll just use the typical sys.excepthook behavior and print a
stacktrace. It's really for debugging problems with the CLI itself, but it
might also come in handy if we have issues with the way that we're trying to
format an exception.
Define an except hook per exception type that we want to treat specially,
generally types of SDK errors, and dispatch onto tht set of hooks.
"""
import sys

import click
from globus_sdk import exc
from six import reraise

from globus_cli.parsing.command_state import CommandState
from globus_cli.safeio import PrintableErrorField, safeprint, write_error_info


def exit_with_mapped_status(http_status):
    """
    Given an HTTP Status, exit with either an error status of 1 or the
    status mapped by what we were given.
    """
    # get the mapping by looking up the state and getting the mapping attr
    mapping = click.get_current_context().ensure_object(CommandState).http_status_map

    # if there is a mapped exit code, exit with that. Otherwise, exit 1
    if http_status in mapping:
        sys.exit(mapping[http_status])
    else:
        sys.exit(1)


def session_hook(exception):
    """
    Expects an exception with an authorization_paramaters field in its raw_json
    """
    safeprint(
        "The resource you are trying to access requires you to "
        "re-authenticate with specific identities."
    )

    params = exception.raw_json["authorization_parameters"]
    message = params.get("session_message")
    if message:
        safeprint("message: {}".format(message))

    identities = params.get("session_required_identities")
    if identities:
        id_str = " ".join(identities)
        safeprint(
            "Please run\n\n"
            "    globus session update {}\n\n"
            "to re-authenticate with the required identities".format(id_str)
        )
    else:
        safeprint(
            'Please use "globus session update" to re-authenticate '
            "with specific identities".format(id_str)
        )

    exit_with_mapped_status(exception.http_status)


def transferapi_hook(exception):
    write_error_info(
        "Transfer API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("request_id", exception.request_id),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )
    exit_with_mapped_status(exception.http_status)


def authapi_hook(exception):
    write_error_info(
        "Auth API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )
    exit_with_mapped_status(exception.http_status)


def globusapi_hook(exception):
    write_error_info(
        "GLobus API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )
    exit_with_mapped_status(exception.http_status)


def authentication_hook(exception):
    write_error_info(
        "No Authentication Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
        message=(
            "Globus CLI Error: No Authentication provided. Make sure "
            "you have logged in with 'globus login'."
        ),
    )
    exit_with_mapped_status(exception.http_status)


def invalidrefresh_hook(exception):
    write_error_info(
        "Invalid Refresh Token",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
        message=(
            "Globus CLI Error: Your credentials are no longer "
            "valid. Please log in again with 'globus login'."
        ),
    )
    exit_with_mapped_status(exception.http_status)


def globus_generic_hook(exception):
    write_error_info(
        "Globus Error",
        [
            PrintableErrorField("error_type", exception.__class__.__name__),
            PrintableErrorField("message", str(exception), multiline=True),
        ],
    )
    sys.exit(1)


def custom_except_hook(exc_info):
    """
    A custom excepthook to present python errors produced by the CLI.
    We don't want to show end users big scary stacktraces if they aren't python
    programmers, so slim it down to some basic info. We keep a "DEBUGMODE" env
    variable kicking around to let us turn on stacktraces if we ever need them.

    Additionally, does global suppression of EPIPE errors, which often occur
    when a python command is piped to a consumer like `head` which closes its
    input stream before python has sent all of its output.
    DANGER: There is a (small) risk that this will bite us if there are EPIPE
    errors produced within the Globus SDK. We should keep an eye on this
    possibility, as it may demand more sophisticated handling of EPIPE.
    Possible TODO item to reduce this risk: inspect the exception and only hide
    EPIPE if it comes from within the globus_cli package.
    """
    exception_type, exception, traceback = exc_info

    # check if we're in debug mode, and run the real excepthook if we are
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    if state.debug:
        sys.excepthook(exception_type, exception, traceback)

    # we're not in debug mode, do custom handling
    else:

        # if it's a click exception, re-raise as original -- Click's main
        # execution context will handle pretty-printing
        if isinstance(exception, click.ClickException):
            reraise(exception_type, exception, traceback)

        # catch any session errors to give helpful instructions
        # on how to use globus session update
        elif (
            isinstance(exception, exc.GlobusAPIError)
            and exception.raw_json
            and "authorization_parameters" in exception.raw_json
        ):
            session_hook(exception)

        # handle the Globus-raised errors with our special hooks
        # these will present the output (on stderr) as JSON
        elif isinstance(exception, exc.TransferAPIError):
            if exception.code == "ClientError.AuthenticationFailed":
                authentication_hook(exception)
            else:
                transferapi_hook(exception)

        elif isinstance(exception, exc.AuthAPIError):
            if exception.code == "UNAUTHORIZED":
                authentication_hook(exception)
            # invalid_grant occurs when the users refresh tokens are not valid
            elif exception.message == "invalid_grant":
                invalidrefresh_hook(exception)
            else:
                authapi_hook(exception)

        elif isinstance(exception, exc.GlobusAPIError):
            globusapi_hook(exception)

        # specific checks fell through -- now check if it's any kind of
        # GlobusError
        elif isinstance(exception, exc.GlobusError):
            globus_generic_hook(exception)

        # not a GlobusError, not a ClickException -- something like ValueError
        # or NotImplementedError bubbled all the way up here: just print it
        # out, basically
        else:
            safeprint(u"{}: {}".format(exception_type.__name__, exception))
            sys.exit(1)
