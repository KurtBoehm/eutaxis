# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, final

from .licenses import License, license_header
from .repository import project_url

cpp_headers: Final[set[str]] = {
    "algorithm",
    "any",
    "array",
    "atomic",
    "barrier",
    "bit",
    "bitset",
    "cassert",
    "cctype",
    "cerrno",
    "cfenv",
    "cfloat",
    "charconv",
    "chrono",
    "cinttypes",
    "climits",
    "clocale",
    "cmath",
    "codecvt",
    "compare",
    "complex",
    "concepts",
    "condition_variable",
    "coroutine",
    "csetjmp",
    "csignal",
    "cstdarg",
    "cstddef",
    "cstdint",
    "cstdio",
    "cstdlib",
    "cstring",
    "ctime",
    "cuchar",
    "cwchar",
    "cwctype",
    "deque",
    "exception",
    "execution",
    "expected",
    "filesystem",
    "flat_map",
    "flat_set",
    "format",
    "forward_list",
    "fstream",
    "functional",
    "future",
    "generator",
    "initializer_list",
    "iomanip",
    "ios",
    "iosfwd",
    "iostream",
    "istream",
    "iterator",
    "latch",
    "limits",
    "list",
    "locale",
    "map",
    "mdspan",
    "memory",
    "memory_resource",
    "mutex",
    "new",
    "numbers",
    "numeric",
    "optional",
    "ostream",
    "print",
    "queue",
    "random",
    "ranges",
    "ratio",
    "regex",
    "scoped_allocator",
    "semaphore",
    "set",
    "shared_mutex",
    "source_location",
    "span",
    "spanstream",
    "sstream",
    "stack",
    "stacktrace",
    "stdexcept",
    "stdfloat",
    "stop_token",
    "streambuf",
    "string",
    "string_view",
    "strstream",
    "syncstream",
    "system_error",
    "thread",
    "tuple",
    "type_traits",
    "typeindex",
    "typeinfo",
    "unordered_map",
    "unordered_set",
    "utility",
    "valarray",
    "variant",
    "vector",
    "version",
    "assert.h",
    "ctype.h",
    "errno.h",
    "fenv.h",
    "float.h",
    "inttypes.h",
    "limits.h",
    "locale.h",
    "math.h",
    "setjmp.h",
    "signal.h",
    "stdarg.h",
    "stddef.h",
    "stdint.h",
    "stdio.h",
    "stdlib.h",
    "string.h",
    "time.h",
    "uchar.h",
    "wchar.h",
    "wctype.h",
}
header_suffixes: Final[set[str]] = {".hpp", ".ipp"}
cpp_suffixes: Final[set[str]] = header_suffixes | {".cpp"}


@dataclass
class Includes:
    cpp: list[str] = field(default_factory=list)
    system: list[str] = field(default_factory=list)
    source: list[str] = field(default_factory=list)
    project: list[str] = field(default_factory=list)
    relative: list[str] = field(default_factory=list)

    @property
    def combined(self) -> str:
        groups = [self.cpp, self.system, self.source, self.project, self.relative]
        return "\n\n".join(
            "\n".join(f"#include {name}" for name in sorted(group))
            for group in groups
            if group
        )


@dataclass
class SpanIncludes:
    begin: int
    _end: int
    includes: Includes
    _ext_end: int | None = None

    @property
    def ext_end(self) -> int:
        return self._ext_end if self._ext_end is not None else self.end

    @ext_end.setter
    def ext_end(self, value: int) -> None:
        self._ext_end = value

    @property
    def end(self) -> int:
        return self._end

    @end.setter
    def end(self, value: int) -> None:
        self._end = value
        self._ext_end = None


@final
class CppRefactor:
    def __init__(self, proj_path: Path, proj_name: str) -> None:
        self.proj_path = proj_path
        self.proj_name = proj_name
        self.write_num = 0

    def recurse(self, path: Path, fn: Callable[[Path], bool]) -> None:
        for p in sorted(path.iterdir()):
            if fn(p):
                self.recurse(p, fn)

    def header_guard_name(self, path: Path) -> str:
        rel = str(path.relative_to(self.proj_path))
        for ch in ("-", ".", "/"):
            rel = rel.replace(ch, "_")
        return rel.upper()

    def write(self, path: Path, contents: str) -> None:
        print("change", path)
        self.write_num += 1
        path.write_text(contents, encoding="utf8")

    def find_headers(self, path: Path) -> Iterable[Path]:
        for p in path.iterdir():
            if p.suffix in header_suffixes:
                yield p

    def generate_parent_header(self, header: Path, children: list[str]) -> str:
        guard = self.header_guard_name(header)
        lines = [
            f"#ifndef {guard}",
            f"#define {guard}",
            "",
            "// IWYU pragma: begin_exports",
            *[f'#include "{child}"' for child in children],
            "// IWYU pragma: end_exports",
            "",
            f"#endif // {guard}",
        ]
        return "\n".join(lines) + "\n"

    def fix_header_guards(
        self,
        base: Path,
        ignore_parent_header: set[Path],
        ignore_folders: set[Path],
    ) -> None:
        def inner(path: Path) -> bool:
            if path.is_dir():
                if path in ignore_folders:
                    return False

                header = path.with_name(f"{path.name}.hpp")
                children = [
                    str(p.relative_to(path.parent))
                    for p in sorted(self.find_headers(path))
                    if p.suffix in header_suffixes
                ]
                contents = self.generate_parent_header(header, children)

                original = (
                    header.read_text(encoding="utf8") if header.exists() else None
                )
                if original != contents and path not in ignore_parent_header:
                    self.write(header, contents)
                return True

            if path.is_file() and path.suffix in header_suffixes:
                orig_contents = path.read_text(encoding="utf8")
                raw_lines = content_lines = orig_contents.splitlines()

                def is_skippable(line: str) -> bool:
                    stripped = line.strip()
                    return not stripped or stripped.startswith("//")

                start = 0
                while start < len(content_lines) and is_skippable(content_lines[start]):
                    start += 1
                content_lines = content_lines[start:]

                assert content_lines, f"{path} is invalid!"
                assert content_lines[0].startswith("#ifndef"), f"{path} is invalid!"
                assert content_lines[1].startswith("#define"), f"{path} is invalid!"
                assert content_lines[-1].startswith("#endif"), f"{path} is invalid!"

                guard = self.header_guard_name(path)
                content_lines[0] = f"#ifndef {guard}"
                content_lines[1] = f"#define {guard}"
                content_lines[-1] = f"#endif // {guard}"

                content_lines = raw_lines[:start] + content_lines
                contents = "\n".join(content_lines) + "\n"
                if orig_contents != contents:
                    self.write(path, contents)
            return False

        self.recurse(base, inner)

    def fix_meson(self, base_path: Path) -> None:
        if not base_path.exists():
            return

        def to_pascal_case(txt: str) -> str:
            parts = txt.split("-")
            return "".join(p[:1].upper() + p[1:] for p in parts if p)

        sources = sorted(
            p.relative_to(base_path) for p in base_path.iterdir() if p.suffix == ".cpp"
        )
        meson_path = base_path / "meson.build"
        meson = meson_path.read_text(encoding="utf8")

        prefix = "foreach name, info : {\n"
        suffix = "\n}\n"
        start_idx = meson.find(prefix)
        end_idx = meson.find(suffix)

        if start_idx == -1 or end_idx == -1 or end_idx < start_idx:
            return

        start = start_idx + len(prefix)
        lines = "\n".join(
            f"  '{to_pascal_case(s.stem)}': [['{s}'], []]," for s in sources
        )
        out = f"{meson[:start]}{lines}{meson[end_idx:]}"

        if meson != out:
            self.write(meson_path, out)

    def fix_includes(self, base_path: Path, *, ignore_folders: set[Path]) -> None:
        def inner(path: Path) -> bool:
            if path.is_dir():
                return path not in ignore_folders

            if path.suffix in cpp_suffixes and not path.with_name(path.stem).is_dir():
                original = path.read_text(encoding="utf8")
                span_includes: list[SpanIncludes] = []

                header_lines: list[str] = []
                for i, raw_line in enumerate(original.splitlines(keepends=True)):
                    header_lines.append(raw_line)
                    line = raw_line.strip()

                    if line.startswith("#include"):
                        if span_includes and span_includes[-1].ext_end == i:
                            si = span_includes.pop()
                            si.end = i + 1
                        else:
                            si = SpanIncludes(i, i + 1, Includes())

                        fname = line[len("#include") :].strip()
                        name = fname
                        comment_idx = name.find("//")
                        if comment_idx >= 0:
                            name = name[:comment_idx].strip()
                        # strip quotes or < >
                        name = name[1:-1]

                        if fname.startswith('"'):
                            if (path.parent / name).exists():
                                si.includes.relative.append(fname)
                            elif name.split("/", 1)[0] == self.proj_name:
                                si.includes.project.append(fname)
                            else:
                                si.includes.source.append(fname)
                        else:
                            if name in cpp_headers:
                                si.includes.cpp.append(fname)
                            else:
                                si.includes.system.append(fname)

                        span_includes.append(si)

                    if not line and span_includes and span_includes[-1].ext_end == i:
                        span_includes[-1].ext_end = i + 1

                if span_includes:
                    out = ""
                    start = 0
                    for si in span_includes:
                        out += (
                            "".join(header_lines[start : si.begin])
                            + si.includes.combined
                            + "\n"
                        )
                        start = si.end
                    out += "".join(header_lines[start:])

                    if original != out:
                        self.write(path, out)

            return False

        if base_path.exists():
            self.recurse(base_path, inner)

    def fix_qualifiers(self, inc_path: Path) -> None:
        def inner(path: Path) -> bool:
            if path.is_dir():
                return True

            contents = path.read_text(encoding="utf8")
            original = contents

            for src, dst in [("constexpr explicit", "explicit constexpr")]:
                contents = contents.replace(src, dst)

            if original != contents:
                self.write(path, contents)

            return False

        self.recurse(inc_path, inner)

    def fix_base_header(self, inc_path: Path) -> None:
        header = inc_path / f"{inc_path.name}.hpp"
        children = [
            str(p.relative_to(inc_path))
            for p in sorted(self.find_headers(inc_path))
            if p.suffix in header_suffixes and p != header
        ]
        contents = self.generate_parent_header(header, children)

        original = header.read_text(encoding="utf8") if header.exists() else None
        if original != contents:
            self.write(header, contents)

    def fix_license(
        self,
        inc_path: Path,
        *,
        license: License,
        ignore_folders: set[Path],
        url: str | None = None,
    ) -> None:
        if url is None:
            url = project_url(self.proj_path)

        header = license_header(license, "//")
        prefix = f"// This file is part of {url}.\n//\n{header}"

        def inner(p: Path) -> bool:
            if p.is_dir():
                return p not in ignore_folders

            if p.suffix not in (".hpp", ".cpp"):
                return False

            txt = p.read_text(encoding="utf8")
            if not txt or txt.startswith(prefix):
                return False

            lines = [line.strip() for line in txt.splitlines()]
            first_non_comment = [
                line
                for line in lines
                if line and not line.startswith("#") and not line.startswith("//")
            ]
            if not first_non_comment:
                return False

            self.write(p, prefix + "\n\n" + txt)
            return False

        self.recurse(inc_path, inner)
