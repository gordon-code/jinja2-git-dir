from __future__ import annotations

from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, run
from typing import TYPE_CHECKING

from jinja2.ext import Extension

if TYPE_CHECKING:
    from jinja2.environment import Environment


def _normalize_str(str_output: str) -> str:
    return str_output.strip().lower()


def _git_dir(git_path: str) -> bool:
    opts: list[str] = ["rev-parse", "--show-toplevel"]
    git_root_dir: str | None = _run_git_command_at_path(git_path, opts)
    if git_root_dir:
        return _normalize_str(git_root_dir) == _normalize_str(str(Path(git_path).resolve()))

    return False


def _empty_git(git_path: str) -> bool:
    opts: list[str] = ["rev-list", "--all", "--count"]
    num_commits: str | None = _run_git_command_at_path(git_path, opts)

    try:
        num_commits = int(num_commits)  # type: ignore
    except (ValueError, TypeError):
        return False
    else:
        return num_commits == 0


def _run_git_command_at_path(git_path: str, git_opts: list[str]) -> str | None:
    # Utilize Path() to sanitize the input and resolve to an absolute path
    try:
        git_path = str(Path(git_path).resolve())
    except TypeError:
        return None

    try:
        result: CompletedProcess[str] = run(  # noqa: S603
            ["git", "-C", git_path, *git_opts],  # noqa: S607
            check=True,
            capture_output=True,
            encoding="utf-8",
        )
    except CalledProcessError:
        return None
    else:
        return result.stdout


class GitDirectoryExtension(Extension):
    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)
        environment.filters["gitdir"] = _git_dir
        environment.filters["emptygit"] = _empty_git
