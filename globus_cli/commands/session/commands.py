from globus_cli.commands.session.show import session_show
from globus_cli.commands.session.update import session_update
from globus_cli.parsing import globus_group


@globus_group(name="session", help="Manage your CLI auth session")
def session_command():
    pass


# commands
session_command.add_command(session_update)
session_command.add_command(session_show)
