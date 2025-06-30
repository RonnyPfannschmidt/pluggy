# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "rich",
# ]
# ///
from __future__ import annotations

import argparse
import contextlib
import os.path
import shlex
import subprocess
import sys
from pathlib import Path
from contextlib import chdir

from collections.abc import Sequence
from typing import NoReturn, Generator


def ensure(args: list[str], cwd: str | None = None) -> None:
    print("$", shlex.join(args))
    if os.path.isdir(".venv"):

        new_path = f".venv/bin{os.pathsep}{os.environ['PATH']}"
    else:
        new_path = os.environ["PATH"]
    res = subprocess.run(args, cwd=cwd, env={**os.environ, "PATH": new_path})
    if res.returncode:
        print("$", shlex.join(args), "failed")
        sys.exit(res.returncode)

def ensure_install(deps: Sequence[str]):
    ensure(["uv", "venv"])
    ensure([
        *("uv", "pip", "install"),
        *("--python", ".venv/bin/python"),
        *("-e", "../.."),

        *deps,
    ])




@contextlib.contextmanager
def with_downstream_project_directory(
        name: str, git_url: str, depth: int | None = 1
) -> Generator[None, None, None]:
    if os.path.isdir(name):
        ensure(["git", "pull"], cwd=name)
    else:
        if depth is not None:
            depth_args = [f"--depth={depth}"]
        else:
            depth_args = []
        ensure(["git", "clone", *depth_args, git_url, name])
    with chdir(name):
        yield


@with_downstream_project_directory("hatch", git_url="https://github.com/pypa/hatch" )
def hatch(extra_args: Sequence[str]):
    Path("pytest.ini").touch()
    ensure_install([
        *("-e", ".", "-e", "backend",),
        *("pytest", "pytest-xdist"),
        *("trustme", "editables"),

    ])
    # todo: figure correct commands
    ensure([".venv/bin/pytest", "--rootdir=.", "-n8", *extra_args])

@with_downstream_project_directory("datasette", "https://github.com/simonw/datasette")
def datasette(extra_args: Sequence[str]):
    ensure_install(["-e", ".[test]", "click<8.2", "pytest-asyncio<1"])
    # broken
    deselect = ["-k", "not test_serve_localhost_http and not test_serve_unix_domain_socket"]
    ensure([".venv/bin/pytest",*deselect, *extra_args])

@with_downstream_project_directory("pytest", "https://github.com/pytest-dev/pytest", depth=None)
def pytest(extra_args: Sequence[str]):
    ensure_install(["-e", ".[testing]", "setuptools", "attrs", "pytest-xdist","hypothesis", "xmlschema"])
    ensure([".venv/bin/pytest", "-n8", *extra_args])

@with_downstream_project_directory("tox", "https://github.com/tox-dev/tox")
def tox(extra_args: Sequence[str]):
    ensure_install(["-e", ".[testing]"])
    ensure([".venv/bin/pytest", *extra_args])

@with_downstream_project_directory("devpi", "https://github.com/devpi/devpi")
def devpi(extra_args: Sequence[str]):
    ensure_install(["-r", "dev-requirements.txt"])
    ensure([".venv/bin/pytest", "common", *extra_args])
    ensure([".venv/bin/pytest", "server", *extra_args])
    ensure([".venv/bin/pytest", "client", *extra_args])
    ensure([".venv/bin/pytest", "web", *extra_args])

@with_downstream_project_directory("conda", "https://github.com/conda/conda")
def conda(extra_args: Sequence[str]):
    # conda has a special dev setup script, but we'll use direct pip install
    ensure(["bash", "-c", """
    set -x -o pipefail
    source dev/start
    set -eu
    pip install -e ../..
    pytest -m "not integration and not installed"
    """])



def main(args: Sequence[str]|None = None) -> NoReturn:
    if args is None:
        args = sys.argv[1:]

    if not args:
        print("! command missing pick one of:")
        for obj in globals().values():
            if (
                callable(obj) and
                obj.__module__ == __name__ and
                obj not in (with_downstream_project_directory, ensure, ensure_install, main)
            ):
                print("-", obj.__name__)
        sys.exit(1)
    command, *extra_args = args

    func = globals()[command]
    return func(extra_args)



if __name__ == "__main__":
    main()