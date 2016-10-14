import os
from configobj import ConfigObj

import globus_sdk
import globus_sdk.config

from globus_cli import version

__all__ = [
    # option name constants
    'OUTPUT_FORMAT_OPT',
    'AUTH_RT_OPTNAME',
    'TRANSFER_RT_OPTNAME',

    'internal_auth_client',

    'get_auth_refresh_token',
    'get_transfer_refresh_token',

    'write_option',
    'lookup_option',
]


# constant for use throughout the SDK whenever we need to do things using the
# CLI Native App definition
# accessed via `internal_auth_client()` -- not exported
CLIENT_ID = '95fdeba8-fac2-42bd-a357-e068d82ff78e'
# an extra option (not exported) for using the CLI against other Globus
# Environments (like the future beta environment)
ENV_CLIENT_ID_OPTNAME = 'cli_client_id'

# constants for global use
OUTPUT_FORMAT_OPT = ('cli', 'output_format')
AUTH_RT_OPTNAME = 'auth_refresh_token'
TRANSFER_RT_OPTNAME = 'transfer_refresh_token'

# get the environment from env var (not exported)
GLOBUS_ENV = os.environ.get('GLOBUS_SDK_ENVIRONMENT')

# if the env is set, rewrite the refresh token option names to have it as a
# prefix
if GLOBUS_ENV:
    AUTH_RT_OPTNAME = '{0}_auth_refresh_token'.format(GLOBUS_ENV)
    TRANSFER_RT_OPTNAME = '{0}_transfer_refresh_token'.format(GLOBUS_ENV)


def _get_config_obj(system=False):
    # FIXME: DRY violation with config_commands.helpers
    if system:
        path = '/etc/globus.cfg'
    else:
        path = os.path.expanduser("~/.globus.cfg")

    return ConfigObj(path)


def lookup_option(option, section='cli', environment=None):
    p = globus_sdk.config._get_parser()
    return p.get(option, section=section, environment=environment)


def write_option(option, value, section='cli', system=False):
    """
    Write an option to disk -- doesn't handle config reloading
    """
    # deny rwx to Group and World -- don't bother storing the returned old mask
    # value, since we'll never restore it in the CLI anyway
    # do this on every call to ensure that we're always consistent about it
    os.umask(0o077)

    # FIXME: DRY violation with config_commands.helpers
    conf = _get_config_obj(system=system)

    # add the section if absent
    if section not in conf:
        conf[section] = {}

    conf[section][option] = value
    conf.write()


def get_auth_refresh_token():
    return lookup_option(AUTH_RT_OPTNAME)


def get_transfer_refresh_token():
    return lookup_option(TRANSFER_RT_OPTNAME)


def internal_auth_client():
    # check to see if an alternate client ID has been specified by the
    # environment
    client_id = lookup_option(ENV_CLIENT_ID_OPTNAME,
                              environment=GLOBUS_ENV) or CLIENT_ID

    return globus_sdk.NativeAppAuthClient(client_id, app_name=version.app_name)
