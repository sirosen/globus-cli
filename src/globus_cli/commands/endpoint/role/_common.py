import click


def role_id_arg(f):
    return click.argument("role_id")(f)
