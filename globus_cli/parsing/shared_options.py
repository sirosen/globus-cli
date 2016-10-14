import click

from globus_cli.version import __version__
from globus_cli.parsing.command_state import format_option
from globus_cli.parsing.case_insensitive_choice import CaseInsensitiveChoice
from globus_cli.parsing.config_loaded_option import ConfigLoadedOption


def common_options(*args, **kwargs):
    """
    This is a multi-purpose decorator for applying a "base" set of options
    shared by all commands.
    It has two modes of operation.

    Mode I: Basic Behavior
    Apply as a decorator that consumes a single callable as its only argument.
    This is typical decorator syntax "without arguments" as in
    >>> @common_options
    >>> def mycommand(abc, xyz):
    >>>     ...

    Note that `common_options` doesn't have parens, so it's taking `mycommand`
    as its only argument, and as a positional argument.

    Mode II: Customized by Keywords
    Apply as a decorator that takes keyword arguments of its own. In this case,
    `common_options` is a higher order function that produces a decorator,
    based on its keyword arguments. This is used to change or override
    behaviors that are seen in more typical "Mode I" usage. For example
    >>> @common_options(no_format_option=True)
    >>> def mycommand(abc, xyz):
    >>>     ...

    In this case, `common_options` sees no `*args` and a `**kwargs` containing
    `{'no_format_option': True}`
    It produces and returns a decorator based on that optional argument, which
    is, in turn, applied to `mycommand`.
    """
    def decorate(f, **kwargs):
        """
        Work of actually decorating a function -- wrapped in here because we
        want to dispatch depending on how `common_options` is invoked
        """
        f = click.version_option(__version__)(f)
        f = click.help_option('-h', '--help')(f)

        # if the format option is being allowed, it needs to be applied to `f`
        if not kwargs.get('no_format_option'):
            f = format_option(f)

        return f

    # special behavior when invoked with only one non-keyword argument: act as
    # a normal decorator, decorating and returning that argument with
    # click.option
    if len(args) == 1 and len(kwargs) == 0 and callable(args[0]):
        return decorate(args[0])

    # if we're not doing that, we should see no positional args
    # the alternative behavior is to fall through and discard *args, but this
    # will probably confuse someone in the future when their arguments are
    # silently discarded
    elif len(args) != 0:
        raise ValueError(
            'common_options() cannot take positional args')

    # final case: got 0 or more kwargs, no positionals
    # do the function-which-returns-a-decorator dance to produce a
    # new decorator based on the arguments given
    else:
        def inner_decorator(f):
            return decorate(f, **kwargs)
        return inner_decorator


def endpoint_id_option(*args, **kwargs):
    """
    This is the `--endpoint-id` option consumed by many Transfer endpoint
    related operations. It accepts variable helptext, but can also be applied
    as a direct decorator.

    Usage:

    >>> @endpoint_id_option
    >>> def command_func(endpoint_id):
    >>>     ...

    or

    >>> @endpoint_id_option(help='ID of the Share')
    >>> def command_func(endpoint_id):
    >>>     ...
    """
    def decorate(f, **kwargs):
        """
        Work of actually decorating a function -- wrapped in here because we
        want to dispatch depending on how this is invoked
        """
        help = kwargs.get('help', 'ID of the Endpoint')
        f = click.option('--endpoint-id', required=True, help=help,
                         cls=ConfigLoadedOption,
                         config_key=('cli transfer', 'endpoint_id'))(f)
        return f

    # special behavior when invoked with only one non-keyword argument: act as
    # a normal decorator, decorating and returning that argument with
    # click.option
    if len(args) == 1 and len(kwargs) == 0:
        return decorate(args[0])

    # if we're not doing that, we should see no positional args
    # the alternative behavior is to fall through and discard *args, but this
    # will probably confuse someone in the future when their arguments are
    # silently discarded
    elif len(args) != 0:
        raise ValueError(
            'endpoint_id_option() cannot take positional args')

    # final case: got 0 or more kwargs, no positionals
    # do the function-which-returns-a-decorator dance to produce a
    # new decorator based on the arguments given
    else:
        def inner_decorator(f):
            return decorate(f, **kwargs)
        return inner_decorator


def endpoint_create_and_update_opts(create=False, shared_ep=False):
    """
    Collection of options consumed by Transfer endpoint create and update
    operations -- in addition to shared endpoint create and update.
    It accepts toggles regarding create vs. update and shared EP vs. normal EP,
    but can also be applied as a direct decorator.

    Importantly, when given `shared_ep=True`, the options it applies are more
    limited -- so the signature of the decorated function is different.

    Usage:

    >>> @endpoint_create_and_update_opts
    >>> def command_func(display_name, description, organization,
    >>>                  contact_email, contact_info, info_link, public,
    >>>                  default_directory, force_encryption, oauth_server,
    >>>                  myproxy_server, myproxy_dn):
    >>>     ...

    or

    >>> @endpoint_create_and_update_opts(create=False)
    >>> def command_func(display_name, description, organization,
    >>>                  contact_email, contact_info, info_link, public,
    >>>                  default_directory, force_encryption, oauth_server,
    >>>                  myproxy_server, myproxy_dn):
    >>>     ...

    or

    >>> @endpoint_create_and_update_opts(shared_ep=True)
    >>> def command_func(display_name, description, organization,
    >>>                  contact_email, contact_info, info_link, public):
    >>>     ...
    """
    def _mkopt(*args, **kwargs):
        # ensure that diffhelp gets removed -- otherwise, click.option will see
        # it and be sad
        if kwargs.pop('diffhelp', False) and not create:
            kwargs['help'] = 'New ' + kwargs['help']

        return click.option(*args, **kwargs)

    def inner_decorator(f):
        ep_or_share = 'Share'
        if not shared_ep:
            ep_or_share = 'Endpoint'
            f = _mkopt('--myproxy-dn',
                       help=('Only available on Globus Connect Server. '
                             'Set the MyProxy Server DN'))(f)
            f = _mkopt('--myproxy-server',
                       help=('Only available on Globus Connect Server. '
                             'Set the MyProxy Server URI'))(f)
            f = _mkopt('--oauth-server',
                       help=('Only available on Globus Connect Server. '
                             'Set the OAuth Server URI'))(f)
            f = _mkopt('--force-encryption/--no-force-encryption',
                       default=None,
                       help=('Only available on Globus Connect Server. '
                             '(Un)Force transfers to use encryption'))(f)
            f = _mkopt('--default-directory',
                       help=('Only available on Globus Connect Server. '
                             'Set the default directory'))(f)
        f = _mkopt('--public/--private', 'public',
                   help='Set the {0} to be public or private'
                   .format(ep_or_share))(f)
        f = _mkopt('--info-link', diffhelp=True,
                   help='Link for Info about the {0}'.format(ep_or_share))(f)
        f = _mkopt('--contact-info', diffhelp=True,
                   help='Contact Info for the {0}'.format(ep_or_share))(f)
        f = _mkopt('--contact-email', diffhelp=True,
                   help='Contact Email for the {0}'.format(ep_or_share))(f)
        f = _mkopt('--organization', diffhelp=True,
                   help='Organization for the {0}'.format(ep_or_share))(f)
        f = _mkopt('--description', diffhelp=True,
                   help='Description for the {0}'.format(ep_or_share))(f)
        f = _mkopt('--display-name', required=create, diffhelp=True,
                   help='Name for the {0}'.format(ep_or_share))(f)
        return f
    return inner_decorator


def task_id_option(helptext='ID of the Task'):
    """
    This is the `--task-id` option consumed by many Transfer Task operations.
    It accepts variable helptext, and cannot be applied as a direct decorator
    -- it must have arguments, even if they are empty.

    Usage:

    >>> @task_id_option()
    >>> def command_func(task_id):
    >>>     ...

    or

    >>> @task_id_option(helptext='ID of Task to inspect')
    >>> def command_func(task_id):
    >>>     ...
    """
    def inner_decorator(f):
        f = click.option('--task-id', required=True, help=helptext)(f)
        return f
    return inner_decorator


def submission_id_option(f):
    """
    Simple decorator that attaches an option to a command for consuming a
    submission ID, i.e. --submission-id
    """
    f = click.option(
        '--submission-id', help=(
            'Task submission ID, as generated by `globus transfer task '
            'generate-submission-id`. Used for safe resubmission in the '
            'presence of network failures.'))(f)
    return f


def role_id_option(f):
    """
    Unmodifiable `--role-id` option for Transfer Endpoint Role management.
    """
    f = click.option('--role-id', required=True, help='ID of the Role')(f)
    return f


def server_id_option(f):
    """
    Unmodifiable `--server-id` option for Transfer Endpoint Server management.
    """
    f = click.option('--server-id', required=True, help='ID of the Server')(f)
    return f


def server_add_and_update_opts(add=False):
    """
    Shared collection of options for `globus transfer endpoint server add` and
    `globus transfer endpoint server update`.
    Cannot be applied directly -- requires arguments even if they are empty.
    Takes a toggle to know if it's being used as `add` or `update`.

    Usage:

    >>> @server_add_and_update_opts()
    >>> def command_func(subject, port, scheme, hostname):
    >>>     ...

    or

    >>> @server_add_and_update_opts(add=True)
    >>> def command_func(subject, port, scheme, hostname):
    >>>     ...
    """
    def inner_decorator(f):
        f = click.option('--hostname', required=add,
                         help='Server Hostname.')(f)

        default_scheme = 'gsiftp' if add else None
        f = click.option(
            '--scheme', help='Scheme for the Server.',
            type=CaseInsensitiveChoice(('gsiftp', 'ftp')),
            default=default_scheme, show_default=add)(f)

        default_port = 2811 if add else None
        f = click.option(
            '--port', help='Port for Globus control channel connections.',
            type=int, default=default_port, show_default=add)(f)

        f = click.option(
            '--subject',
            help=('Subject of the X509 Certificate of the server. When '
                  'unspecified, the CN must match the server hostname.'))(f)

        return f
    return inner_decorator
