# 🧹 Eutaxis

[![PyPI - Version](https://img.shields.io/pypi/v/eutaxis?logo=pypi&label=PyPI)](https://pypi.org/project/eutaxis/)
[![Test Workflow Status](https://img.shields.io/github/actions/workflow/status/KurtBoehm/eutaxis/test.yml?logo=github&label=Tests)](https://github.com/KurtBoehm/eutaxis/actions/workflows/test.yml)

Eutaxis (from Ancient Greek _εὖ_ “good” + _τάξις_ “arrangement, ordering”) is a command-line tool for normalizing and cleaning up project code layouts.
It focuses on consistent headers, include ordering, and formatting across common project structures.

Currently supported:

- Python projects:
  - `isort` and `ruff`
  - optional licence headers
- Meson projects:
  - Lark-based argument reordering for many functions
  - `muon fmt`
  - optional licence headers
- C++ projects:
  - header guards
  - include ordering
  - Meson targets
  - simple qualifier reordering
  - optional licence headers

## 📦 Installation

Eutaxis is [available on PyPI](https://pypi.org/project/eutaxis/) and can be installed as usual, for example:

```bash
pip install eutaxis
```

## 🚀 Usage

Eutaxis is driven by “workers” (one per language):

```bash
eutaxis <worker> [options]
```

Examples:

```bash
# Clean a Python project in the current directory
eutaxis python

# Clean a Meson project
eutaxis meson -c muon.cfg

# Clean a C++ project using .eutaxis config
eutaxis cpp
```

To see options:

```bash
eutaxis -h
eutaxis python -h
eutaxis meson -h
eutaxis cpp -h
```

## ⚙️ C++ Configuration

C++ clean-up is configured via a `.eutaxis` YAML file in the project root, for example:

```yaml
fix_meson: false
license: MPL-2.0
url: https://github.com/your/repo
project_name: mylib
ignore_parent_header:
  - include/mylib/detail
ignore_folders:
  - external
```

The C++ worker expects the following layout:

- headers: `include/<project_name>/...`
- sources (optional): `src/`, `test/`, `perf/`, `tools/`

## 🧠 Behaviour Overview

- Licence/file headers:
  - Inserts or normalizes licence/file headers for supported languages.
- C++:
  - Normalizes header guards.
  - Maintains “base headers” `<dir>.hpp` with an IWYU export block.
  - Re-sorts and groups includes into:
    - C++ standard headers
    - other system headers
    - project headers
    - relative headers
  - Adjusts a few qualifiers (e.g. `constexpr explicit` → `explicit constexpr`).
  - Updates Meson snippets for per-source targets.
- Python and Meson:
  - Runs formatters:
    - Python: `isort`, `ruff format`
    - Meson: Lark-based argument reordering for many functions, `muon fmt`

## ⌨️ Shell Completion

Eutaxis integrates with [`argcomplete`](https://github.com/kislyuk/argcomplete).
Once `argcomplete` is installed and enabled in your shell,

```bash
eutaxis <TAB>
```

can be used to complete available workers and options.

## 📜 Licence

This library is licensed under the terms of the Mozilla Public Licence 2.0, provided in [`License`](https://github.com/KurtBoehm/eutaxis/blob/main/License).
