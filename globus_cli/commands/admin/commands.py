from globus_cli.commands.admin.task import task_command
from globus_cli.parsing import globus_group


@globus_group(
    name="admin", help="Perform advanced endpoint management functions as an admin"
)
def admin_command():
    pass


admin_command.add_command(task_command)
