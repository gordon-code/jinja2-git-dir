from inspect import getsourcefile
from pathlib import Path

import pytest
from jinja2 import Environment

project_root_path = Path(getsourcefile(lambda: 0)).resolve().parent.parent


@pytest.fixture
def environment():
    return Environment(extensions=["jinja2_git_dir.GitDirectoryExtension"])  # noqa: S701


@pytest.mark.parametrize(
    ("git_path", "toplevel_git_dir", "expected", "mock_subprocess"),
    [
        # cwd == "tests/" directory
        (project_root_path, project_root_path, "True", False),
        ("/git-dir", "/git-dir", "True", True),
        ("/Git-Dir", "/git-dir", "True", True),
        ("/non-git-dir", "/", "False", True),
        (["not", "a", "path"], "/", "False", False),
    ],
)
def test_git_dir(git_path, toplevel_git_dir, expected, mock_subprocess, environment, fp):  # noqa: PLR0913
    command = ["git", "-C", git_path, "rev-parse", "--show-toplevel"]
    if mock_subprocess:
        # Mock the subprocess result
        fp.register(command, stdout=toplevel_git_dir, occurrences=3)
    else:
        fp.allow_unregistered(allow=True)

    # Test the rendered template
    template = environment.from_string("{{ git_path | gitdir }}")
    assert template.render(git_path=git_path) == expected

    template = environment.from_string("{{ git_path | gitdir is true }}")
    assert template.render(git_path=git_path) == expected

    template = environment.from_string("{% if (git_path | gitdir) %}True{% else %}False{% endif %}")
    assert template.render(git_path=git_path) == expected
