from pathlib import Path
from subprocess import CalledProcessError, CompletedProcess, run

from jinja2.environment import Environment
from jinja2.ext import Extension


def _git_dir(git_path: str) -> bool:
    # Utilize Path() to sanitize the input and resolve to an absolute path
    try:
        git_path = str(Path(git_path).resolve())
    except TypeError:
        return False
    command: list[str] = ["git", "-C", git_path, "rev-parse", "--show-toplevel"]
    try:
        result: CompletedProcess[str] = run(command, check=True, capture_output=True, text=True)  # noqa: S603
        return result.stdout.lower() == git_path
    except CalledProcessError:
        return False


class GitDirectoryExtension(Extension):
    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)
        environment.filters["gitdir"] = _git_dir
