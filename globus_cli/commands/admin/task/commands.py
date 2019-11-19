from globus_cli.commands.admin.task.show import show_task
from globus_cli.parsing import globus_group


@globus_group(name="task", help="Manage asynchronous tasks as admin")
def task_command():
    pass


task_command.add_command(show_task)
