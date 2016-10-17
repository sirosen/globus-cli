from globus_cli.parsing.main_command_decorator import globus_main_func

from globus_cli.parsing.case_insensitive_choice import CaseInsensitiveChoice
from globus_cli.parsing.hidden_option import HiddenOption
from globus_cli.parsing.aliases import AliasCommand

from globus_cli.parsing.shared_options import (
    common_options,
    endpoint_id_option, task_id_option, submission_id_option,
    endpoint_create_and_update_opts, role_id_option,
    server_id_option, server_add_and_update_opts)


__all__ = [
    'globus_main_func',

    'CaseInsensitiveChoice',
    'HiddenOption',
    'AliasCommand',

    'common_options',
    # Transfer options
    'endpoint_id_option', 'task_id_option', 'submission_id_option',
    'endpoint_create_and_update_opts', 'role_id_option',
    'server_id_option', 'server_add_and_update_opts',
]
