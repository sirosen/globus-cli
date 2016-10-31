import textwrap
import click
import subprocess

from globus_cli.version import __version__
from globus_cli.parsing.hidden_option import HiddenOption


class CommandWithMan(click.Command):
    def __init__(self, *args, **kwargs):
        self.manpage_example = kwargs.pop('manpage_example', None)
        self.manpage_description = kwargs.pop('manpage_description', None)
        super(CommandWithMan, self).__init__(*args, **kwargs)

    def generate_manpage(self):
        ctx = click.get_current_context()

        # title line is fixed for each command
        title_line = textwrap.dedent("""\
        .TH "{0}" "1" "{1}" "{2}" "{3} Manual"
        """).format(self.name.upper(),
                    "2016", __version__, ctx.command_path)

        # name section is actually just the command name and the short help
        name_section = '.SH NAME\n{0} \\- {1}'.format(
            self.name, self.short_help)

        # synopsis is the usage text
        synopsis_section = textwrap.dedent("""\
        .SH SYNOPSIS
        .B {0}
        {1}
        """).format(self.name, ' '.join(self.collect_usage_pieces(ctx)))

        # description is a section for manpages to give a more detailed
        # explanation of what the command does -- for this purpose we use the
        # base help text
        # however, to apply more information here, a command may supply
        # additional description info
        description_section = textwrap.dedent("""\
        .SH DESCRIPTION
        {0}

        {1}
        """).format(self.help, textwrap.dedent(self.manpage_description or ''))

        options = ((p.opts, p.help or '',
                    p.make_metavar() if not p.is_flag else None)
                   for p in self.params
                   if isinstance(p, click.Option) and
                   not isinstance(p, HiddenOption))
        option_lines = [
            '.IP ' + ' '.join(
                '"{}"'.format(
                    o + (' ' + metavar) if metavar else ''
                ) for o in opts) +
            '\n{}'.format(helpstr)
            for (opts, helpstr, metavar) in options
        ]
        options_section = textwrap.dedent("""\
        .SH OPTIONS
        {0}
        """).format('\n'.join(option_lines))

        # example is a custom section for manpages to give  usage examples
        example_section = (textwrap.dedent("""\
        .SH EXAMPLE
        {0}
        """).format(textwrap.dedent(self.manpage_example))
            if self.manpage_example else None)

        return '\n'.join(x for x in
                         (title_line, name_section, synopsis_section,
                          options_section, description_section,
                          example_section)
                         if x)


def command_with_man(*args, **kwargs):
    cmd = click.command(*args, cls=CommandWithMan, **kwargs)

    def decorate(f):
        def callback(ctx, param, value):
            if not value or ctx.resilient_parsing:
                return
            p = subprocess.Popen(['man', '/dev/stdin'], stdin=subprocess.PIPE)
            p.communicate(input=ctx.command.generate_manpage())
            p.wait()
            ctx.exit(0)

        f = click.option('--man', is_eager=True, callback=callback,
                         is_flag=True, expose_value=False,
                         help=('Open a manpage with `man`. Only works on '
                               'platforms where `man` is present'))(f)
        return cmd(f)

    return decorate
