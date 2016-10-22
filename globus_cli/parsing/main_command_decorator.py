"""
This module defines all of the tools needed to decorate the top-level `globus`
command. All customizations that apply specifically to this main command go
here.
Ultimately, `globus_cli.parsing` will export only the decorator defined here,
and all other components will be hidden internals.
"""

import sys
import click

from globus_cli.parsing.shell_completion import shell_complete_option
from globus_cli.parsing.excepthook import custom_except_hook
from globus_cli.parsing.shared_options import common_options


class TopLevelGroup(click.Group):
    """
    This is a custom command type which is basically a click.Group, but is
    designed specifically for the top level command.
    It's specialization is that it catches all exceptions from subcommands and
    passes them to a custom error handler.
    """
    def invoke(self, ctx):
        try:
            return super(TopLevelGroup, self).invoke(ctx)
        except Exception:
            custom_except_hook(sys.exc_info())


def globus_main_func(f):
    f = click.group('globus', cls=TopLevelGroup)(f)
    f = common_options(f)
    f = shell_complete_option(f)
    return f
