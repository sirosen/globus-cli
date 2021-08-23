import functools
from typing import Callable, Optional

import click


def task_id_arg(f: Optional[Callable] = None, *, required=True):
    """
    By default, the task ID is made required; pass `required=False` to the
    decorator arguments to make it optional.
    """
    if f is None:
        return functools.partial(task_id_arg, required=required)
    return click.argument("TASK_ID", required=required)(f)
