from inspect import getsourcefile
from pathlib import Path

import pytest
from jinja2 import Environment

project_root_path = Path(getsourcefile(lambda: 0)).resolve().parent.parent


@pytest.fixture
def environment():
    return Environment(extensions=["jinja2_git_dir.GitDirectoryExtension"])  # noqa: S701


@pytest.mark.parametrize(
    ("git_path", "mocked_toplevel_git_dir", "expected"),
    [
        (project_root_path, None, "True"),
        ("/git-dir", "/git-dir", "True"),
        ("/Git-Dir", "/git-dir", "True"),
        ("/non-git-dir", "/", "False"),
        (["not", "a", "path"], None, "False"),
    ],
)
def test_git_dir(git_path, mocked_toplevel_git_dir, expected, environment, fp):
    command = ["git", "-C", git_path, "rev-parse", "--show-toplevel"]
    if mocked_toplevel_git_dir:
        # Mock the subprocess result
        fp.register(command, stdout=mocked_toplevel_git_dir, occurrences=4)
    else:
        fp.allow_unregistered(allow=True)

    # Test the rendered template
    template = environment.from_string("{{ git_path | gitdir }}")
    assert template.render(git_path=git_path) == expected

    template = environment.from_string("{{ git_path | gitdir is true }}")
    assert template.render(git_path=git_path) == expected

    template = environment.from_string("{{ git_path | gitdir is false }}")
    assert template.render(git_path=git_path) != expected

    template = environment.from_string("{% if (git_path | gitdir) %}True{% else %}False{% endif %}")
    assert template.render(git_path=git_path) == expected


@pytest.mark.parametrize(
    ("git_path", "mocked_num_commits", "expected"),
    [
        (project_root_path, None, "False"),
        ("/git-dir", "0", "True"),
        ("/Git-Dir", "1", "False"),
        ("/non-git-dir", "", "False"),
        (["not", "a", "path"], None, "False"),
        ("/my-path", "not-a-number", "False"),
    ],
)
def test_empty_git(git_path, mocked_num_commits, expected, environment, fp):
    command = ["git", "-C", git_path, "rev-list", "--all", "--count"]
    if mocked_num_commits:
        # Mock the subprocess result
        fp.register(command, stdout=mocked_num_commits, occurrences=4)
    else:
        fp.allow_unregistered(allow=True)

    # Test the rendered template
    template = environment.from_string("{{ git_path | emptygit }}")
    assert template.render(git_path=git_path) == expected

    template = environment.from_string("{{ git_path | emptygit is true }}")
    assert template.render(git_path=git_path) == expected

    template = environment.from_string("{{ git_path | emptygit is false }}")
    assert template.render(git_path=git_path) != expected

    template = environment.from_string("{% if (git_path | emptygit) %}True{% else %}False{% endif %}")
    assert template.render(git_path=git_path) == expected
