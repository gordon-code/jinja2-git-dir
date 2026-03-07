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


def _parse_symbolic_ref(output: str) -> str:
    stripped = output.strip()
    if stripped and "/" in stripped:
        return stripped.split("/")[-1]
    return ""


def _parse_ls_remote_symref(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("ref: refs/heads/"):
            ref_path = line.split("\t")[0]
            return ref_path.split("/")[-1]
    return ""


def _git_default_branch(git_path: str) -> str:
    # Not a git repo → empty string
    if _run_git_command_at_path(git_path, ["rev-parse", "--is-inside-work-tree"]) is None:
        return ""

    # Try symbolic-ref for upstream, then origin (local, fast)
    for remote in ("upstream", "origin"):
        result = _run_git_command_at_path(git_path, ["symbolic-ref", f"refs/remotes/{remote}/HEAD"])
        if result:
            branch = _parse_symbolic_ref(result)
            if branch:
                return branch

    # Try ls-remote for upstream, then origin (network, read-only)
    for remote in ("upstream", "origin"):
        result = _run_git_command_at_path(git_path, ["ls-remote", "--symref", remote, "HEAD"])
        if result:
            branch = _parse_ls_remote_symref(result)
            if branch:
                return branch

    # Try git config init.defaultBranch
    result = _run_git_command_at_path(git_path, ["config", "init.defaultBranch"])
    if result and result.strip():
        return result.strip()

    # Ultimate fallback
    return "main"


def _empty_git(git_path: str) -> bool:
    opts: list[str] = ["rev-list", "--all", "--count"]
    num_commits: str | None = _run_git_command_at_path(git_path, opts)

    try:
        num_commits = int(num_commits)  # type: ignore[arg-type]
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
        environment.filters["gitdefaultbranch"] = _git_default_branch
