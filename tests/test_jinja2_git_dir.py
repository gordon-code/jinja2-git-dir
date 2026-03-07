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
        ("/git-dir", "/git-dir\n", "True"),
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
    ("git_path", "mock_commands", "expected"),
    [
        # Cascade level 1: upstream symbolic-ref
        (
            "/git-dir",
            {
                ("git", "-C", "/git-dir", "rev-parse", "--is-inside-work-tree"): "true",
                (
                    "git",
                    "-C",
                    "/git-dir",
                    "symbolic-ref",
                    "refs/remotes/upstream/HEAD",
                ): "refs/remotes/upstream/develop",
            },
            "develop",
        ),
        # Cascade level 2: origin symbolic-ref (upstream fails)
        (
            "/git-dir",
            {
                ("git", "-C", "/git-dir", "rev-parse", "--is-inside-work-tree"): "true",
                ("git", "-C", "/git-dir", "symbolic-ref", "refs/remotes/origin/HEAD"): "refs/remotes/origin/main\n",
            },
            "main",
        ),
        # Cascade level 3: ls-remote upstream
        (
            "/git-dir",
            {
                ("git", "-C", "/git-dir", "rev-parse", "--is-inside-work-tree"): "true",
                (
                    "git",
                    "-C",
                    "/git-dir",
                    "ls-remote",
                    "--symref",
                    "upstream",
                    "HEAD",
                ): "ref: refs/heads/master\tHEAD\nabc123\tHEAD\n",
            },
            "master",
        ),
        # Cascade level 4: ls-remote origin
        (
            "/git-dir",
            {
                ("git", "-C", "/git-dir", "rev-parse", "--is-inside-work-tree"): "true",
                (
                    "git",
                    "-C",
                    "/git-dir",
                    "ls-remote",
                    "--symref",
                    "origin",
                    "HEAD",
                ): "ref: refs/heads/trunk\tHEAD\nabc123\tHEAD\n",
            },
            "trunk",
        ),
        # Cascade level 5: git config init.defaultBranch
        (
            "/git-dir",
            {
                ("git", "-C", "/git-dir", "rev-parse", "--is-inside-work-tree"): "true",
                ("git", "-C", "/git-dir", "config", "init.defaultBranch"): "master\n",
            },
            "master",
        ),
        # Cascade level 6: hardcoded fallback "main"
        (
            "/git-dir",
            {
                ("git", "-C", "/git-dir", "rev-parse", "--is-inside-work-tree"): "true",
            },
            "main",
        ),
        # Not a git repo → empty string
        ("/non-git-dir", {}, ""),
        # Invalid path type → empty string
        (["not", "a", "path"], {}, ""),
    ],
)
def test_git_default_branch(git_path, mock_commands, expected, environment, fp):
    # Register mocked commands that should succeed
    for cmd, stdout in mock_commands.items():
        fp.register(list(cmd), stdout=stdout)

    # Let unregistered commands fail (CalledProcessError)
    fp.allow_unregistered(allow=True)

    template = environment.from_string("{{ git_path | gitdefaultbranch }}")
    assert template.render(git_path=git_path) == expected


def test_git_default_branch_conditional(environment, fp):
    """Test gitdefaultbranch in a conditional — non-empty string is truthy."""
    fp.register(
        ["git", "-C", "/git-dir", "rev-parse", "--is-inside-work-tree"],
        stdout="true",
    )
    fp.allow_unregistered(allow=True)

    template = environment.from_string("{% if (git_path | gitdefaultbranch) %}yes{% else %}no{% endif %}")
    assert template.render(git_path="/git-dir") == "yes"
    assert template.render(git_path="/non-git-dir") == "no"


@pytest.mark.parametrize(
    ("git_path", "mocked_num_commits", "expected"),
    [
        (project_root_path, None, "False"),
        ("/git-dir", "0", "True"),
        ("/git-dir", "0\n", "True"),
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
