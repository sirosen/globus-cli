import json
import click

from globus_sdk import TransferData

from globus_cli.parsing import (
    CaseInsensitiveChoice, common_options, submission_id_option,
    TaskPath, ENDPOINT_PLUS_OPTPATH, shlex_process_stdin,
    command_with_man)
from globus_cli.safeio import safeprint
from globus_cli.helpers import (
    outformat_is_json, print_json_response, colon_formatted_print)

from globus_cli.services.transfer import get_client, autoactivate


@command_with_man('transfer', short_help='Submit a Transfer Task',
                  help=("Copy a file or directory (or set of files and "
                        "directories) from one Endpoint to "
                        "another as an asynchronous task."),
                  manpage_description=("""\
    .B "Single-Item Mode vs. Batch Mode"

    .RS
    This command two modes of operation: single-item, and batchmode.

    Single-item has behavior similar to
    .I cp
    and
    .IR "cp -r",
    across endpoints of course. It is the behavior you get if you use
    .I SOURCE_PATH
    and
    .IR DEST_PATH .

    Batch Mode is the way in which `transfer` can be used to
    submit a Task which transfers multiple files or directories, and it is
    used to accept paths to transfer on stdin.
    .RE

    .B Batch Mode
    .RS
    Batchmode splits each line on spaces, and treats every line as a file or
    directory item to transfer.

    Splitting is done using Python shlex in POSIX mode:
    .I https://docs.python.org/2/library/shlex.html

    Lines are of the form
    .RS
    [--recursive] SOURCE_PATH DEST_PATH
    .RE

    Skips empty lines and allows comments beginning with
    .IR # .

    You can use
    .I --batch
    with a commandline
    .IR SOURCE_PATH " and/or " DEST_PATH ,
    in which case these paths will be used as dir prefixes to any paths in the
    batch input.
    .RE

    .B Sync Levels
    .RS
    Sync Levels are ways in which the Task determines whether or not to
    actually move a file over the network.
    Choosing a higher sync level will reduce your network traffic when files in
    your transfer already exist on the destination, but will increase local IO
    and CPU load marginally at each end of the transfer.
    We recommend using high sync levels for tasks where you know or suspect
    that a non-negligible percentage of files already exist on the destination.

    .IP EXISTS
    Determine whether or not to transfer based on file existence.
    If the destination file is absent, do the transfer.

    .IP SIZE
    Determine whether or not to transfer based on the size of the file.
    If destination file size does not match the source, do the transfer.

    .IP MTIME
    Determine whether or not to transfer based on modification times.
    If source has a newer modififed time than the destination, do the transfer.

    .IP CHECKSUM
    Determine whether or not to transfer based on checksums of file contents.
    If source and destination contents differ, as determined by a checksum of
    their contents, do the transfer.
    .RE
    """),
                  manpage_example=("""\
    Example of --batch usage:

        $ cat dat
        # file 1, simple
        ~/dir1/sourcepath1 /abspath/destpath1

        # file 2, with spaces in dest path
        # paths without / or ~ are relative to the default_directory of the
        # endpoint they are on
        dir2/sourcepath2   "path with spaces/dest2"

        # dir 1, requires --recursive option
        --recursive ~/srcdir1/ /somepath/destdir1

        $ cat dat | globus transfer \\\\
            --batch --sync-level checksum \\\\
            "$SOURCE_ENDPOINT_ID" "$DEST_ENDPOINT_ID"
    """))
@common_options
@submission_id_option
@click.option('--dry-run', is_flag=True,
              help=("Don't actually perform the transfer, print submission "
                    "data instead"))
@click.option('--recursive', is_flag=True,
              help=('SOURCE_PATH and DEST_PATH are both directories, do a '
                    'recursive dir transfer'))
@click.option('--label', default=None, help=('Set a label for this task.'))
@click.option('--sync-level', default=None, show_default=True,
              type=CaseInsensitiveChoice(
                  ("exists", "size", "mtime", "checksum")),
              help=('How will the Transfer Task determine whether or not to '
                    'actually transfer a file over the network?'))
@click.option('--preserve-mtime', is_flag=True, default=False,
              help=('Preserve file and directory modification times.'))
@click.option('--verify-checksum/--no-verify-checksum', default=True,
              show_default=True,
              help=('Verify checksum after transfer.'))
@click.option('--encrypt', is_flag=True, default=False,
              help=('Encrypt data sent through the network.'))
@click.option('--batch', is_flag=True,
              help=('Accept a batch of source/dest path pairs on stdin (i.e. '
                    'run in batchmode). '
                    'Uses SOURCE_ENDPOINT_ID and DEST_ENDPOINT_ID as passed '
                    'on the commandline'))
@click.argument('source', metavar='SOURCE_ENDPOINT_ID[:SOURCE_PATH]',
                type=ENDPOINT_PLUS_OPTPATH)
@click.argument('destination', metavar='DEST_ENDPOINT_ID[:DEST_PATH]',
                type=ENDPOINT_PLUS_OPTPATH)
def transfer_command(batch, sync_level, recursive, destination, source, label,
                     preserve_mtime, verify_checksum, encrypt, submission_id,
                     dry_run):
    """
    Executor for `globus transfer`
    """
    source_endpoint, cmd_source_path = source
    dest_endpoint, cmd_dest_path = destination

    if recursive and batch:
        raise click.UsageError(
            ('You cannot use --recursive in addition to --batch. '
             'Instead, use --recursive on lines of --batch input '
             'which need it'))

    if (cmd_source_path is None or cmd_dest_path is None) and (not batch):
        raise click.UsageError(
            ('transfer requires either SOURCE_PATH and DEST_PATH or '
             '--batch'))

    client = get_client()
    transfer_data = TransferData(
        client, source_endpoint, dest_endpoint,
        label=label, sync_level=sync_level, verify_checksum=verify_checksum,
        preserve_timestamp=preserve_mtime, encrypt_data=encrypt)

    if batch:
        @click.command()
        @click.option('--recursive', is_flag=True)
        @click.argument('source_path', type=TaskPath(base_dir=cmd_source_path))
        @click.argument('dest_path', type=TaskPath(base_dir=cmd_dest_path))
        def process_batch_line(dest_path, source_path, recursive):
            """
            Parse a line of batch input and turn it into a transfer submission
            item.
            """
            transfer_data.add_item(str(source_path), str(dest_path),
                                   recursive=recursive)

        shlex_process_stdin(
            process_batch_line,
            ('Enter transfers, line by line, as\n\n'
             '    [--recursive] SOURCE_PATH DEST_PATH\n'))
    else:
        transfer_data.add_item(cmd_source_path, cmd_dest_path,
                               recursive=recursive)

    if submission_id is not None:
        transfer_data['submission_id'] = submission_id

    if dry_run:
        # don't bother dispatching out output format -- just print as JSON
        safeprint(json.dumps(transfer_data, indent=2))
        # exit safely
        return

    # autoactivate after parsing all args and putting things together
    autoactivate(client, source_endpoint, if_expires_in=60)
    autoactivate(client, dest_endpoint, if_expires_in=60)

    res = client.submit_transfer(transfer_data)

    if outformat_is_json():
        print_json_response(res)
    else:
        fields = (('Message', 'message'), ('Task ID', 'task_id'))
        colon_formatted_print(res, fields)
