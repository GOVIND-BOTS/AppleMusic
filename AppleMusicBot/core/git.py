import asyncio
import base64
import shlex
from typing import Tuple

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

import config

from ..logging import LOGGER


def install_req(cmd: str) -> Tuple[str, str, int, int]:
    async def install_requirements():
        args = shlex.split(cmd)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()
        return (
            stdout.decode("utf-8", "replace").strip(),
            stderr.decode("utf-8", "replace").strip(),
            process.returncode,
            process.pid,
        )

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(install_requirements())

    raise RuntimeError(
        "install_req() cannot run inside an active event loop; "
        "run dependency installation during synchronous startup."
    )


def _git_auth_environment(repo):
    """Return a temporary Git environment without storing credentials in origin."""
    if not config.GIT_TOKEN:
        return repo.git.custom_environment()

    credentials = base64.b64encode(
        f"x-access-token:{config.GIT_TOKEN}".encode("utf-8")
    ).decode("ascii")

    return repo.git.custom_environment(
        GIT_CONFIG_COUNT="1",
        GIT_CONFIG_KEY_0="http.extraheader",
        GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {credentials}",
    )


def git():
    upstream_repo = config.UPSTREAM_REPO
    upstream_branch = config.UPSTREAM_BRANCH

    try:
        repo = Repo()
        LOGGER(__name__).info("Git repository found [VPS deployer].")
        return

    except InvalidGitRepositoryError:
        repo = Repo.init()
    except GitCommandError as exc:
        LOGGER(__name__).error(f"Git command failed: {exc}")
        raise

    # Always keep the saved remote URL credential-free.
    if "origin" in repo.remotes:
        origin = repo.remote("origin")
        origin.set_url(upstream_repo)
    else:
        origin = repo.create_remote("origin", upstream_repo)

    try:
        with _git_auth_environment(repo):
            origin.fetch(upstream_branch)

            remote_ref = origin.refs[upstream_branch]
            local_branch = (
                repo.heads[upstream_branch]
                if upstream_branch in repo.heads
                else repo.create_head(upstream_branch, remote_ref)
            )
            local_branch.set_tracking_branch(remote_ref)
            local_branch.checkout(True)

            try:
                origin.pull(upstream_branch)
            except GitCommandError:
                repo.git.reset("--hard", "FETCH_HEAD")

        LOGGER(__name__).info("Fetched upstream repository successfully.")

    except Exception as exc:
        LOGGER(__name__).error(
            "Could not fetch upstream repository: "
            f"{type(exc).__name__}: {exc}"
        )
        raise

    stdout, stderr, returncode, _ = install_req(
        "pip3 install --no-cache-dir -r requirements.txt"
    )
    if returncode:
        LOGGER(__name__).error(
            f"Dependency installation failed: {stderr or stdout}"
        )
        raise RuntimeError("Could not install requirements.txt dependencies.")

    LOGGER(__name__).info("Upstream dependencies installed successfully.")
