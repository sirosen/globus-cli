import os.path
import textwrap
import click

from globus_cli.safeio import safeprint
from globus_cli.parsing import CaseInsensitiveChoice, common_options
from globus_cli.config import write_option, OUTPUT_FORMAT_OPT


@click.command('init',
               help=('Initialize your Globus Config file with any settings '
                     'you may want for the SDK and CLI'))
@common_options(no_format_option=True)
@click.option('--default-output-format',
              help='The default format for the CLI to use when printing.',
              type=CaseInsensitiveChoice(['json', 'text']))
def init_command(default_output_format):
    """
    Executor for `globus config init`
    """
    # now handle the output format, requires a little bit more care
    # first, prompt if it isn't given, but be clear that we have a sensible
    # default if they don't set it
    # then, make sure that if it is given, it's a valid format (discard
    # otherwise)
    # finally, set it only if given and valid
    if not default_output_format:
        safeprint(textwrap.fill(
            'This must be one of "json" or "text". Other values will be '
            'ignored. ENTER to skip.'))
        default_output_format = click.prompt(
            'Default CLI output format (output_format)',
            default='text',
            ).strip().lower()
        if default_output_format not in ('json', 'text'):
            default_output_format = None

    # write to disk
    safeprint('\n\nWriting updated config to {0}'
              .format(os.path.expanduser('~/.globus.cfg')))
    section, optname = OUTPUT_FORMAT_OPT
    write_option(optname, default_output_format, section=section)
