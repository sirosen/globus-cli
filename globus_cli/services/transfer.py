from __future__ import print_function

import json

from globus_sdk import TransferClient

from globus_cli.helpers import outformat_is_json, outformat_is_text


def _display_name_or_cname(ep_doc):
    return ep_doc['display_name'] or ep_doc['canonical_name']


def _print_json_from_iterator(iterator):
    json_output_dict = {'DATA': []}
    for item in iterator:
        json_output_dict['DATA'].append(item)
    print(json.dumps(json_output_dict))


def _text_header_and_format(lengths_and_headers):
    format_lengths = [max(l, len(h)) for (l, h) in lengths_and_headers]
    format_str = ' | '.join('{:' + str(l) + '}' for l in format_lengths)

    print(format_str.format(*[h for (l, h) in lengths_and_headers]))
    print(format_str.format(*['-'*l for l in format_lengths]))

    return format_str


def _endpoint_list_to_text(iterator):
    text_col_format = _text_header_and_format(
        [(32, 'Owner'), (36, 'ID'), (None, 'Display Name')])

    for result in iterator:
        print(text_col_format.format(
            result['owner_string'], result['id'],
            _display_name_or_cname(result)))


def endpoint_search(args):
    """
    Executor for `globus transfer endpoint-search`
    """
    client = TransferClient()
    search_iterator = client.endpoint_search(
        filter_fulltext=args.fulltext, filter_scope=args.scope)

    if outformat_is_json(args):
        _print_json_from_iterator(search_iterator)
    else:
        _endpoint_list_to_text(search_iterator)


def endpoint_autoactivate(args):
    """
    Executor for `globus transfer endpoint-autoactivate`
    """
    client = TransferClient()
    res = client.endpoint_autoactivate(args.endpoint_id)
    print(res.text_body)


def endpoint_server_list(args):
    """
    Executor for `globus transfer endpoint-server-list`
    """
    client = TransferClient()

    server_iterator = client.endpoint_server_list(args.endpoint_id)

    if outformat_is_json(args):
        _print_json_from_iterator(server_iterator)
    else:
        text_col_format = _text_header_and_format(
            [(36, 'URI')])

        for result in server_iterator:
            print(text_col_format.format(result['uri']))


def my_shared_endpoint_list(args):
    """
    Executor for `globus transfer endpoint-my-shared-endpoint-list`
    """
    client = TransferClient()

    ep_iterator = client.my_shared_endpoint_list(args.endpoint_id)

    if outformat_is_json(args):
        _print_json_from_iterator(ep_iterator)
    else:
        _endpoint_list_to_text(ep_iterator)


def endpoint_role_list(args):
    """
    Executor for `globus transfer endpoint-role-list`
    """
    client = TransferClient()

    role_iterator = client.endpoint_role_list(args.endpoint_id)

    if outformat_is_json(args):
        _print_json_from_iterator(role_iterator)
    else:
        text_col_format = _text_header_and_format(
            [(16, 'Principal Type'), (36, 'Principal'), (16, 'Role')])

        for result in role_iterator:
            print(text_col_format.format(
                result['principal_type'], result['principal'], result['role']))


def endpoint_acl_list(args):
    """
    Executor for `globus transfer endpoint-acl-list`
    """
    client = TransferClient()

    rule_iterator = client.endpoint_acl_list(args.endpoint_id)

    if outformat_is_json(args):
        _print_json_from_iterator(rule_iterator)
    else:
        text_col_format = _text_header_and_format(
            [(16, 'Principal Type'), (36, 'Principal'), (None, 'Permissions'),
             (None, 'Path')])

        for result in rule_iterator:
            print(text_col_format.format(
                result['principal_type'], result['principal'],
                result['permissions'], result['path']))


def bookmark_list(args):
    """
    Executor for `globus transfer bookmark-list`
    """
    client = TransferClient()

    bookmark_iterator = client.bookmark_list()

    if outformat_is_json(args):
        _print_json_from_iterator(bookmark_iterator)
    else:
        text_col_format = _text_header_and_format(
            [(32, 'Name'), (36, 'Endpoint ID'), (None, 'Path')])

        for result in bookmark_iterator:
            print(text_col_format.format(
                result['name'], result['endpoint_id'], result['path']))


def task_list(args):
    """
    Executor for `globus transfer task-list`
    """
    client = TransferClient()

    task_iterator = client.task_list(num_results=10)

    if outformat_is_json(args):
        _print_json_from_iterator(task_iterator)
    else:
        text_col_format = _text_header_and_format(
            [(36, 'Task ID'), (16, 'Status'), (16, 'Type'),
             (36, 'Source'), (36, 'Dest')])

        for result in task_iterator:
            print(text_col_format.format(
                result['task_id'], result['status'], result['type'],
                result['source_endpoint_id'],
                result['destination_endpoint_id']))


def task_event_list(args):
    """
    Executor for `globus transfer task-event-list`
    """
    client = TransferClient()

    event_iterator = client.task_event_list(args.task_id)

    if outformat_is_json(args):
        _print_json_from_iterator(event_iterator)
    else:
        text_col_format = _text_header_and_format(
            [(25, 'Time'), (32, 'Code'), (8, 'Is Error'), (None, 'Details')])

        for result in event_iterator:
            print(text_col_format.format(
                result['time'], result['code'],
                result['is_error'], result['details']))


def op_ls(args):
    """
    Executor for `globus transfer ls`
    """
    client = TransferClient()
    res = client.operation_ls(args.endpoint_id, path=args.path)
    if outformat_is_json(args):
        print(json.dumps(res.json_body))
    else:
        for item in res.json_body['DATA']:
            print(item['name'])


def op_mkdir(args):
    """
    Executor for `globus transfer mkdir`
    """
    client = TransferClient()
    res = client.operation_mkdir(args.endpoint_id, path=args.path)

    if outformat_is_json(args):
        print(res.text_body)
    else:
        print(res.json_body['message'])


def op_rename(args):
    """
    Executor for `globus transfer rename`
    """
    client = TransferClient()
    res = client.operation_rename(args.endpoint_id, oldpath=args.oldpath,
                                  newpath=args.newpath)

    if outformat_is_json(args):
        print(res.text_body)
    else:
        print(res.json_body['message'])
