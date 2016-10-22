import os
import shlex
import click

from globus_cli.safeio import safeprint
from globus_cli.parsing.hidden_option import HiddenOption
from globus_cli.parsing.case_insensitive_choice import CaseInsensitiveChoice

SUPPORTED_SHELLS = ['BASH', 'ZSH']


def safe_split_line(inputline):
    parser = shlex.shlex(inputline, posix=True)
    parser.whitespace_split = True
    res = []
    # track whether or not we're looking at quoted text -- it should suppress a
    # lot of types of completion if we see an open quote without a close quote
    quoted = False
    try:
        for val in parser:
            res.append(val)
    # No closing quotation
    except ValueError:
        quoted = True
    # grab the last token from the shlexer
    if parser.token:
        res.append(parser.token)
    return res, quoted


def get_completion_context(args):
    """
    Walk the tree of commands to a terminal command or multicommand, using the
    Click Context system.
    Effectively, we'll be using the resilient_parsing mode of commands to stop
    evaluation, then having them capture their options and arguments, passing
    us on to the next subcommand. If we walk "off the tree" with a command that
    we don't recognize, we have a hardstop condition, but otherwise, we walk as
    far as we can go and that's the location from which we should do our
    completion work.
    """
    # get the "globus" command as a click.Command
    root_command = click.get_current_context().find_root().command
    # build a new context object off of it, with resilient_parsing set so that
    # no callbacks are invoked
    ctx = root_command.make_context('globus', list(args),
                                    resilient_parsing=True)

    # walk down multicommands until we've matched on everything and are at a
    # terminal context that holds all of our completed args
    while isinstance(ctx.command, click.MultiCommand) and args:
        # trim out any params that are capturable at this level of the command
        # tree by resetting the argument list
        args = ctx.protected_args + ctx.args

        # if there were no remaining args, stop walking the tree
        if not args:
            break

        # check for a matching command, and if one isn't found stop the
        # traversal and abort the whole process -- this would mean that a
        # completed command was entered which doesn't match a known command
        # there's nothing completion can do in this case unless it implements
        # sophisticated fuzzy matching
        command = ctx.command.get_command(ctx, args[0])
        if not command:
            return None

        # otherwise, grab that command, and build a subcontext to continue the
        # tree walk
        else:
            ctx = command.make_context(args[0], args[1:], parent=ctx,
                                       resilient_parsing=True)

    # return the context we found
    return ctx


def get_all_choices(completed_args, cur, quoted):
    ctx = get_completion_context(completed_args)
    if not ctx:
        return []

    # matching rules, so we can toggle by type and such
    def match_with_case(n, m):
        """case matters"""
        return n.startswith(m)

    def match_nocase(n, m):
        """case doesn't matter"""
        return n.lower().startswith(m.lower())

    match_func = match_with_case

    ctx_options = [p for p in ctx.command.get_params(ctx)
                   if isinstance(p, click.Option)]

    last_completed = None
    if completed_args:
        last_completed = completed_args[-1]

    # if the last completed argument matches a Choice option, we're going to
    # have to expand cur as a choice param
    matching_choice_opt = None
    for p in ctx_options:
        if isinstance(p.type, click.Choice) and last_completed in p.opts:
            matching_choice_opt = p

    choices = []
    # if we ended on a choice, complete with all of the available values
    if matching_choice_opt:
        # catch the case where it's case insensitive, and we need to change our
        # comparisons / matching later on
        if isinstance(matching_choice_opt.type, CaseInsensitiveChoice):
            match_func = match_nocase
        choices = matching_choice_opt.type.choices
    # if cur looks like an option, just look for options
    # but skip if it's quoted text
    elif cur and cur.startswith('-') and not quoted:
        for param in ctx_options:
            # skip hidden options
            if isinstance(param, HiddenOption):
                continue
            for opt in param.opts:
                # only add long-opts, never short opts to completion, unless
                # the cur appears to be a short opt already
                if opt.startswith('--') or (
                        len(cur) > 1 and cur[1] != '-'):
                    choices.append(opt)
    # and if it's a multicommand we see, get the list of subcommands
    elif isinstance(ctx.command, click.MultiCommand) and not quoted:
        choices = [name for name in ctx.command.list_commands(ctx)]
    else:
        pass

    # now, do final filtering
    if cur:
        choices = [n for n in choices if match_func(n, cur)]

    return choices


def do_bash_complete():
    comp_words, quoted = safe_split_line(os.environ['COMP_WORDS'])
    cur_index = int(os.environ['COMP_CWORD'])
    try:
        cur = comp_words[cur_index]
        completed_args = comp_words[1:-1]
    except IndexError:
        cur = None
        completed_args = comp_words[1:]

    choices = get_all_choices(completed_args, cur, quoted)

    safeprint('\t'.join(choices), newline=False)
    click.get_current_context().exit(0)


def do_zsh_complete():
    commandline = os.environ['COMMANDLINE']
    comp_words, quoted = safe_split_line(commandline)
    comp_words = comp_words[1:]

    if comp_words and not commandline.endswith(' '):
        cur = comp_words[-1]
        completed_args = comp_words[:-1]
    else:
        cur = None
        completed_args = comp_words

    choices = get_all_choices(completed_args, cur, quoted)

    safeprint("_arguments '*: :(({}))'".format('\n'.join(choices)),
              newline=False)


def shell_complete_option(f):
    def callback(ctx, param, value):
        if not value or ctx.resilient_parsing:
            return

        if value == 'BASH':
            do_bash_complete()
        elif value == 'ZSH':
            do_zsh_complete()
        else:
            raise ValueError('Unsupported shell completion')

        click.get_current_context().exit(0)

    f = click.option('--shell-complete', cls=HiddenOption,
                     is_eager=True, expose_value=False,
                     type=click.Choice(SUPPORTED_SHELLS),
                     callback=callback)(f)
    return f
