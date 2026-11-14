import base64
import shlex
import subprocess
from contextlib import nullcontext
from typing import Tuple

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

import config

from ..logging import LOGGER


def install_req(cmd: str) -> Tuple[str, str, int, int]:
    """Run a dependency command synchronously and return output/status/PID."""
    args = shlex.split(cmd)
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    stdout, stderr = process.communicate()
    return (
        stdout.strip(),
        stderr.strip(),
        process.returncode,
        process.pid,
    )


def _authenticated_git_context(repo):
    """Authenticate GitHub HTTPS requests without saving a token in origin.url."""
    token = config.GIT_TOKEN
    if not token:
        return nullcontext()

    credentials = base64.b64encode(
        f"x-access-token:{token}".encode("utf-8")
    ).decode("ascii")

    return repo.git.custom_environment(
        GIT_CONFIG_COUNT="1",
        GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
        GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {credentials}",
    )


def git():
    upstream = config.UPSTREAM_REPO.strip()
    if not upstream.startswith(("https://", "http://", "git@")):
        raise ValueError("UPSTREAM_REPO must be a valid Git repository URL.")

    try:
        repo = Repo(search_parent_directories=True)
        LOGGER(__name__).info("Git repository found.")
        return repo
    except InvalidGitRepositoryError:
        repo = Repo.init()
    except GitCommandError as exc:
        LOGGER(__name__).error(f"Git initialization failed: {exc}")
        raise

    try:
        if "origin" in repo.remotes:
            origin = repo.remote("origin")
            # Never retain a credential-bearing remote URL.
            origin.set_url(upstream)
        else:
            origin = repo.create_remote("origin", upstream)

        with _authenticated_git_context(repo):
            origin.fetch()

            remote_branch = f"origin/{config.UPSTREAM_BRANCH}"
            if remote_branch not in [ref.name for ref in repo.references]:
                raise RuntimeError(
                    f"Upstream branch '{config.UPSTREAM_BRANCH}' was not found."
                )

            if config.UPSTREAM_BRANCH in repo.heads:
                local_branch = repo.heads[config.UPSTREAM_BRANCH]
                local_branch.set_tracking_branch(
                    repo.remote("origin").refs[config.UPSTREAM_BRANCH]
                )
                local_branch.checkout(force=True)
            else:
                local_branch = repo.create_head(
                    config.UPSTREAM_BRANCH,
                    repo.remote("origin").refs[config.UPSTREAM_BRANCH],
                )
                local_branch.set_tracking_branch(
                    repo.remote("origin").refs[config.UPSTREAM_BRANCH]
                )
                local_branch.checkout(force=True)

            try:
                origin.pull(config.UPSTREAM_BRANCH)
            except GitCommandError:
                repo.git.reset("--hard", "FETCH_HEAD")

        stdout, stderr, returncode, _pid = install_req(
            "pip install --no-cache-dir -r requirements.txt"
        )
        if returncode:
            LOGGER(__name__).error(
                f"Dependency installation failed (exit {returncode}): "
                f"{stderr or stdout}"
            )
            raise RuntimeError("Could not install requirements.txt.")

        LOGGER(__name__).info("Upstream repository synchronized.")
        return repo

    except Exception as exc:
        LOGGER(__name__).exception(
            f"Unable to initialize upstream repository: "
            f"{type(exc).__name__}: {exc}"
        )
        raise
