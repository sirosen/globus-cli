import click

from globus_cli import config
from globus_cli.parsing.case_insensitive_choice import CaseInsensitiveChoice
from globus_cli.parsing.config_loaded_option import ConfigLoadedOption


# Format Enum for output formatting
# could use a namedtuple, but that's overkill
JSON_FORMAT = 'json'
TEXT_FORMAT = 'text'


class CommandState(object):
    def __init__(self):
        self.output_format = None

    def outformat_is_text(self):
        return self.output_format == TEXT_FORMAT

    def outformat_is_json(self):
        return self.output_format == JSON_FORMAT


def format_option(f):
    def callback(ctx, param, value):
        state = ctx.ensure_object(CommandState)
        if value is not None:
            state.output_format = value.lower()

    return click.option(
        '-F', '--format',
        type=CaseInsensitiveChoice([JSON_FORMAT, TEXT_FORMAT]),
        cls=ConfigLoadedOption,
        config_key=config.OUTPUT_FORMAT_OPT,
        help='Output format for stdout',
        default=TEXT_FORMAT, show_default=True,
        expose_value=False, callback=callback)(f)
