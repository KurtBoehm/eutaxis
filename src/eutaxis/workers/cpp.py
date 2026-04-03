# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from argparse import ArgumentParser
from pathlib import Path
from typing import Any, Final, final, override

from pydantic import BaseModel
from yaml import safe_load

from .cpp_refactor import CppRefactor
from .licenses import License
from .worker import Worker


class Config(BaseModel):
    fix_meson: bool = False
    license: License | None = None
    url: str | None = None
    project_name: str | None = None
    project_path: Path | None = None
    ignore_parent_header: list[Path] = []
    ignore_folders: list[Path] = []


class Args(BaseModel):
    project_path: Path | None


@final
class CppWorker(Worker):
    @staticmethod
    @override
    def id() -> str:
        return "cpp"

    @staticmethod
    @override
    def help() -> str:
        return "Clean up C++ code."

    @staticmethod
    @override
    def add_arguments(parser: ArgumentParser) -> None:
        parser.add_argument(
            "project_path",
            type=Path,
            nargs="?",
            help="Path to the project root (defaults to current working directory).",
        )

    @staticmethod
    @override
    def run(raw_args: dict[str, Any]) -> None:
        args = Args.model_validate(raw_args)

        proj_path: Final[Path] = args.project_path or Path.cwd()
        conf_path = proj_path / ".eutaxis"

        if conf_path.exists():
            conf_data = safe_load(conf_path.read_text(encoding="utf8"))
            conf = Config.model_validate(conf_data)
        else:
            conf = Config()

        proj_name = conf.project_name or proj_path.name

        inc_path = proj_path / "include" / proj_name
        source_paths = ["test", "perf", "src", "tools"]
        source_paths = [p for n in source_paths if (p := proj_path / n).exists()]

        header_paths: list[Path] = []
        if inc_path.exists():
            header_paths.append(inc_path)
        header_paths.extend(source_paths)

        ignore_folders = {proj_path / q for q in conf.ignore_folders}
        ignore_parent_header = {proj_path / q for q in conf.ignore_parent_header}

        refactor = CppRefactor(proj_path, proj_name)
        iteration = 0

        while True:
            print(f"Run {iteration}")

            for p in header_paths:
                refactor.fix_header_guards(
                    p,
                    ignore_parent_header=ignore_parent_header,
                    ignore_folders=ignore_folders,
                )

            if conf.fix_meson:
                for p in source_paths:
                    refactor.fix_meson(p)

            for p in header_paths:
                refactor.fix_includes(p, ignore_folders=ignore_folders)

            if inc_path.exists():
                refactor.fix_qualifiers(inc_path)
                refactor.fix_base_header(inc_path)

            if conf.license is not None:
                for p in header_paths:
                    refactor.fix_license(
                        p,
                        license=conf.license,
                        ignore_folders=ignore_folders,
                        url=conf.url,
                    )

            if refactor.write_num == 0:
                break

            refactor.write_num = 0
            iteration += 1
