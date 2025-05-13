import contextlib

import pytest
from jinja2 import Environment


@pytest.fixture
def environment():
    return Environment(extensions=["jinja2_git_dir.GitDirectoryExtension"])  # noqa: S701


@pytest.mark.parametrize(
    ("git_path", "toplevel_git_dir", "expected"),
    [
        ("/git-dir", "/git-dir", "True"),
        ("/Git-Dir", "/git-dir", "True"),
        ("/non-git-dir", "/", "False"),
        (["not", "a", "path"], "/", "False"),
    ],
)
def test_git_dir(git_path, toplevel_git_dir, expected, environment, fp):
    with contextlib.suppress(TypeError):
        # Mock the subprocess result
        # Allow to fail for "unhashable" input, this will be sanitized by the Path conversion
        fp.register(["git", "-C", git_path, "rev-parse", "--show-toplevel"], stdout=toplevel_git_dir, occurrences=3)

    # Test the rendered template
    template = environment.from_string("{{ git_path | gitdir }}")
    assert template.render(git_path=git_path) == expected

    template = environment.from_string("{{ git_path | gitdir is true }}")
    assert template.render(git_path=git_path) == expected

    template = environment.from_string("{% if (git_path | gitdir) %}True{% else %}False{% endif %}")
    assert template.render(git_path=git_path) == expected
