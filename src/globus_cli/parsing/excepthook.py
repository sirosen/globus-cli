"""
Setup a custom except hook which formats exceptions that are uncaught.
In "DEBUGMODE", we'll just use the typical sys.excepthook behavior and print a
stacktrace. It's really for debugging problems with the CLI itself, but it
might also come in handy if we have issues with the way that we're trying to
format an exception.
Define an except hook per exception type that we want to treat specially,
generally types of SDK errors, and dispatch onto tht set of hooks.
"""
import functools
import sys

import click
import click.exceptions
import globus_sdk

from globus_cli.parsing.command_state import CommandState
from globus_cli.termio import PrintableErrorField, write_error_info

_REGISTERED_HOOKS = []


def globusapi_excepthook(condition):
    """decorator for excepthooks

    register each one, in order, with any relevant "condition"
    """

    def inner_decorator(fn):
        @functools.wraps(fn)
        def wrapped(exception):
            fn(exception)
            # get the mapping by looking up the state and getting the mapping attr
            mapping = (
                click.get_current_context().ensure_object(CommandState).http_status_map
            )

            # if there is a mapped exit code, exit with that. Otherwise, exit 1
            if exception.http_status in mapping:
                sys.exit(mapping[exception.http_status])
            sys.exit(1)

        _REGISTERED_HOOKS.append((wrapped, condition))
        return wrapped

    return inner_decorator


@globusapi_excepthook(lambda err: err.info.authorization_parameters)
def session_hook(exception):
    """
    Expects an exception with a valid authorization_paramaters info field
    """
    click.echo(
        "The resource you are trying to access requires you to "
        "re-authenticate with specific identities."
    )

    message = exception.info.authorization_parameters.session_message
    if message:
        click.echo(f"message: {message}")

    identities = exception.info.authorization_parameters.session_required_identities
    domains = exception.info.authorization_parameters.session_required_single_domain
    if identities or domains:
        click.echo(
            (
                "Please run\n\n"
                "    globus session update {}\n\n"
                "to re-authenticate with the required identities"
            ).format(" ".join(identities) if identities else " ".join(domains))
        )
    else:
        click.echo(
            'Please use "globus session update" to re-authenticate '
            "with specific identities"
        )


@globusapi_excepthook(lambda err: err.info.consent_required)
def consent_required_hook(exception):
    """
    Expects an exception with a required_scopes field in its raw_json
    """
    # specialized message for data_access errors
    # otherwise, use more generic phrasing
    if exception.message == "Missing required data_access consent":
        click.echo(
            "The collection you are trying to access data on requires you to "
            "grant consent for the Globus CLI to access it."
        )
    else:
        click.echo(
            "The resource you are trying to access requires you to "
            "consent to additional access for the Globus CLI."
        )
    click.echo(f"message: {exception.message}")

    required_scopes = exception.info.consent_required.required_scopes
    if not required_scopes:
        click.secho(
            "Fatal Error: ConsentRequired but no required_scopes!", bold=True, fg="red"
        )
        sys.exit(255)

    click.echo(
        "\nPlease run\n\n"
        "  globus session consent {}\n\n".format(
            " ".join(f"'{x}'" for x in required_scopes)
        )
        + "to login with the required scopes"
    )


@globusapi_excepthook(
    lambda err: (
        (
            isinstance(err, globus_sdk.TransferAPIError)
            and err.code == "ClientError.AuthenticationFailed"
        )
        or (isinstance(err, globus_sdk.AuthAPIError) and err.code == "UNAUTHORIZED")
    )
)
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


@globusapi_excepthook(lambda err: isinstance(err, globus_sdk.TransferAPIError))
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


@globusapi_excepthook(
    lambda err: isinstance(err, globus_sdk.AuthAPIError)
    and err.message == "invalid_grant"
)
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


@globusapi_excepthook(lambda err: isinstance(err, globus_sdk.AuthAPIError))
def authapi_hook(exception):
    write_error_info(
        "Auth API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )


@globusapi_excepthook(lambda err: True)  # catch-all
def globusapi_hook(exception):
    write_error_info(
        "Globus API Error",
        [
            PrintableErrorField("HTTP status", exception.http_status),
            PrintableErrorField("code", exception.code),
            PrintableErrorField("message", exception.message, multiline=True),
        ],
    )


def custom_except_hook(exc_info):
    """
    A custom excepthook to present python errors produced by the CLI.
    We don't want to show end users big scary stacktraces if they aren't python
    programmers, so slim it down to some basic info. We keep a "DEBUGMODE" env
    variable kicking around to let us turn on stacktraces if we ever need them.
    """
    exception_type, exception, traceback = exc_info

    # check if we're in debug mode, and run the real excepthook if we are
    ctx = click.get_current_context()
    state = ctx.ensure_object(CommandState)
    if state.debug:
        sys.excepthook(exception_type, exception, traceback)

    # we're not in debug mode, do custom handling

    if isinstance(exception, globus_sdk.GlobusAPIError):
        for (handler, condition) in _REGISTERED_HOOKS:
            if not condition(exception):
                continue
            handler(exception)

    # specific checks fell through -- now check if it's any kind of GlobusError
    if isinstance(exception, globus_sdk.GlobusError):
        write_error_info(
            "Globus Error",
            [
                PrintableErrorField("error_type", exception.__class__.__name__),
                PrintableErrorField("message", str(exception), multiline=True),
            ],
        )
        sys.exit(1)

    # if it's a click exception, re-raise as original -- Click's main
    # execution context will handle pretty-printing
    if isinstance(
        exception, (click.ClickException, click.exceptions.Abort, click.exceptions.Exit)
    ):
        raise exception.with_traceback(traceback)

    # not a GlobusError, not a ClickException -- something like ValueError
    # or NotImplementedError bubbled all the way up here: just print it out
    click.echo(
        "{}: {}".format(
            click.style(exception_type.__name__, bold=True, fg="red"), exception
        )
    )
    sys.exit(1)
