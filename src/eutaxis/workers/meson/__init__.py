# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from argparse import ArgumentParser
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Final, final, override

from pydantic import BaseModel

from ..licenses import License, license_header
from ..repository import project_url
from ..worker import Worker


class Args(BaseModel):
    license: License | None
    skip_header: bool
    muon_cfg: Path
    project_path: Path | None


def iterdir_recursive(directory: Path, *, include_wraps: bool) -> Iterable[Path]:
    """Yield Meson-related files under ``d``."""
    for p in sorted(directory.iterdir()):
        if p.is_dir():
            if p.name not in {"packagecache", "subprojects", ".git"}:
                yield from iterdir_recursive(p, include_wraps=include_wraps)
        else:
            if p.name in {"meson.build", "meson_options.txt"}:
                yield p
            elif include_wraps and p.suffix == ".wrap":
                yield p


@final
class MesonWorker(Worker):
    @staticmethod
    @override
    def id() -> str:
        return "meson"

    @staticmethod
    @override
    def help() -> str:
        return "Clean up Meson code."

    @staticmethod
    @override
    def add_arguments(parser: ArgumentParser) -> None:
        parser.add_argument(
            "--license",
            "-l",
            help="License identifier to use when adding headers.",
        )
        parser.add_argument(
            "--skip-header",
            action="store_true",
            help="Do not add or update the license/file header.",
        )
        parser.add_argument(
            "--muon-cfg",
            "-c",
            type=Path,
            required=True,
            help="Path to the muon configuration file.",
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
        from .lark_clean import lark_clean

        args: Final[Args] = Args.model_validate(raw_args)

        proj_path: Final[Path] = args.project_path or Path.cwd()

        all_meson_files = list(iterdir_recursive(proj_path, include_wraps=True))
        if not all_meson_files:
            return

        if not args.skip_header:
            url = project_url(proj_path)
            header = f"# This file is part of {url}.\n"
            if args.license is not None:
                header += "#\n" + license_header(args.license, "#")
            header += "\n"

            for p in all_meson_files:
                text = p.read_text(encoding="utf8")
                if not text.startswith(header):
                    p.write_text(header + text, encoding="utf8")

        fmt_targets = list(iterdir_recursive(proj_path, include_wraps=False))
        if not fmt_targets:
            return

        lark_clean(fmt_targets, config=args.muon_cfg, in_place=True, format=True)
