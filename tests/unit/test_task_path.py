import click

from globus_cli.parsing import TaskPath


def test_task_path_normpath_updir(run_command):
    @click.command()
    @click.option("--bar", type=TaskPath(base_dir="/foo"))
    def foo(bar):
        click.echo(repr(bar))

    result = run_command(foo, ["--bar", "../baz.txt"])
    assert (
        "TaskPath(base_dir=/foo,coerce_to_dir=False,normalize=True,"
        "path=/baz.txt,orig_path=../baz.txt)\n"
    ) == result.output

    # going up "too many dirs" does nothing
    result = run_command(foo, ["--bar", "../../../baz.txt"])
    assert (
        "TaskPath(base_dir=/foo,coerce_to_dir=False,normalize=True,"
        "path=/baz.txt,orig_path=../../../baz.txt)\n"
    ) == result.output


def test_task_path_normpath_updir_no_base(run_command):
    @click.command()
    @click.option("--bar", type=TaskPath())
    def foo(bar):
        click.echo(repr(bar))

    # a ".." based path should be preserved
    result = run_command(foo, ["--bar", "../../../baz.txt"])
    assert (
        "TaskPath(base_dir=None,coerce_to_dir=False,normalize=True,"
        "path=../../../baz.txt,orig_path=../../../baz.txt)\n"
    ) == result.output
    # a ".." based path should be preserved
    result = run_command(foo, ["--bar", "../../../baz/"])
    assert (
        "TaskPath(base_dir=None,coerce_to_dir=False,normalize=True,"
        "path=../../../baz/,orig_path=../../../baz/)\n"
    ) == result.output


def test_task_path_normpath_only_slash(run_command):
    @click.command()
    @click.option("--bar", type=TaskPath())
    def foo(bar):
        click.echo(repr(bar))

    # a path of "/" should be preserved
    result = run_command(foo, ["--bar", "/"])
    assert (
        "TaskPath(base_dir=None,coerce_to_dir=False,normalize=True,"
        "path=/,orig_path=/)\n"
    ) == result.output


def test_task_path_join_slashes(run_command):
    # NOTE: normalize=False so that we get more direct results
    @click.command()
    @click.option("--bar", type=TaskPath(base_dir="/foo/", normalize=False))
    def foo(bar):
        click.echo(repr(bar))

    # absolute paths don't join
    result = run_command(foo, ["--bar", "/baz.txt"])
    assert (
        "TaskPath(base_dir=/foo/,coerce_to_dir=False,normalize=False,"
        "path=/baz.txt,orig_path=/baz.txt)\n"
    ) == result.output
    result = run_command(foo, ["--bar", "/baz/"])
    assert (
        "TaskPath(base_dir=/foo/,coerce_to_dir=False,normalize=False,"
        "path=/baz/,orig_path=/baz/)\n"
    ) == result.output

    # empty paths give you the base path
    result = run_command(foo, ["--bar", ""])
    assert (
        "TaskPath(base_dir=/foo/,coerce_to_dir=False,normalize=False,"
        "path=/foo/,orig_path=)\n"
    ) == result.output

    # slash join any ordinary path
    result = run_command(foo, ["--bar", "baz.txt"])
    assert (
        "TaskPath(base_dir=/foo/,coerce_to_dir=False,normalize=False,"
        "path=/foo/baz.txt,orig_path=baz.txt)\n"
    ) == result.output
    result = run_command(foo, ["--bar", "baz/"])
    assert (
        "TaskPath(base_dir=/foo/,coerce_to_dir=False,normalize=False,"
        "path=/foo/baz/,orig_path=baz/)\n"
    ) == result.output


def test_task_path_require_absolute(run_command):
    @click.command()
    @click.option("--bar", type=TaskPath(require_absolute=True))
    def foo(bar):
        click.echo(repr(bar))

    # absolute paths are fine
    result = run_command(foo, ["--bar", "/baz.txt"])
    assert (
        "TaskPath(base_dir=None,coerce_to_dir=False,normalize=True,"
        "path=/baz.txt,orig_path=/baz.txt)\n"
    ) == result.output
    result = run_command(foo, ["--bar", "/baz/"])
    assert (
        "TaskPath(base_dir=None,coerce_to_dir=False,normalize=True,"
        "path=/baz/,orig_path=/baz/)\n"
    ) == result.output

    # non-absolute paths error
    result = run_command(foo, ["--bar", "baz.txt"], exit_code=2)
    assert "baz.txt is not absolute" in result.output
    result = run_command(foo, ["--bar", "baz/"], exit_code=2)
    assert "baz/ is not absolute" in result.output


def test_task_path_coerce_to_dir(run_command):
    @click.command()
    @click.option("--bar", type=TaskPath(coerce_to_dir=True))
    def foo(bar):
        click.echo(repr(bar))

    # filename -> append slash
    result = run_command(foo, ["--bar", "/baz.txt"])
    assert (
        "TaskPath(base_dir=None,coerce_to_dir=True,normalize=True,"
        "path=/baz.txt/,orig_path=/baz.txt)\n"
    ) == result.output

    # dirname -> no change
    result = run_command(foo, ["--bar", "baz/"])
    assert (
        "TaskPath(base_dir=None,coerce_to_dir=True,normalize=True,"
        "path=baz/,orig_path=baz/)\n"
    ) == result.output
