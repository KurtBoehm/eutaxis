# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Iterable
from pathlib import Path
from subprocess import run as _run
from typing import Any, Final, final, override

from pydantic import BaseModel

from .licenses import License, license_header
from .repository import project_url
from .worker import Worker


class Args(BaseModel):
    license: License | None
    raw_path: bool
    skip_header: bool
    project_path: Path | None


def iterdir_recursive(directory: Path) -> Iterable[Path]:
    """Yield all Python files under ``directory``, skipping cache and VCS dirs."""
    for path in sorted(directory.iterdir()):
        if path.is_dir():
            if path.name not in {"__pycache__", ".git"}:
                yield from iterdir_recursive(path)
        elif path.suffix in {".py", ".pyi"}:
            yield path


@final
class PythonWorker(Worker):
    @staticmethod
    @override
    def id() -> str:
        return "python"

    @staticmethod
    @override
    def help() -> str:
        return "Clean up Python code."

    @staticmethod
    @override
    def add_arguments(parser: ArgumentParser) -> None:
        parser.add_argument(
            "--license",
            "-l",
            help="License identifier to use when adding headers.",
        )
        parser.add_argument(
            "--raw-path",
            "-r",
            action="store_true",
            help="Use the project path directly instead of the “src” sub-directory.",
        )
        parser.add_argument(
            "--skip-header",
            action="store_true",
            help="Do not add or update the license/file header.",
        )
        parser.add_argument(
            "project_path",
            type=Path,
            nargs="?",
            help="Path to the project root (defaults to current working directory).",
        )

    @staticmethod
    @override
    def run(raw_args: dict[str, Any]) -> None:
        args: Final[Args] = Args.model_validate(raw_args)

        project_path: Final[Path] = args.project_path or Path.cwd()

        if args.raw_path:
            search_paths = [project_path]
        else:
            search_paths = [project_path / "src", project_path / "tests"]
            search_paths = [p for p in search_paths if p.exists()]

        paths: Final[list[Path]] = [
            path for directory in search_paths for path in iterdir_recursive(directory)
        ]

        if not paths:
            return

        if not args.skip_header:
            url = project_url(project_path)
            header = f"# This file is part of {url}.\n"
            if args.license is not None:
                header += "#\n" + license_header(args.license, "#")
            header += "\n"

            for path in paths:
                text = path.read_text(encoding="utf8")
                if not text.startswith(header):
                    path.write_text(header + text, encoding="utf8")

        _run(["isort", *paths])
        _run(["ruff", "format", *paths])
