import click

from globus_cli.safeio import safeprint
from globus_cli.parsing import common_options
from globus_cli.config import lookup_option
from globus_cli.config_command.helpers import parse_path_param


@click.command('show', help='Show a value from the Globus Config')
@common_options(no_format_option=True)
@click.argument('parameter', required=True)
def show_command(parameter):
    """
    Executor for `globus config show`
    """
    section, parameter = parse_path_param(parameter)

    value = lookup_option(parameter, section=section)

    if value is None:
        safeprint('{} not set'.format(parameter))
    else:
        safeprint('{} = {}'.format(parameter, value))
