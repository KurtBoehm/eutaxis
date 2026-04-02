# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# PYTHON_ARGCOMPLETE_OK

from __future__ import annotations

from argparse import ArgumentParser

from argcomplete import autocomplete

from .workers import workers

__version__ = "1.1.0"


def run() -> None:
    from pydantic import TypeAdapter

    parser = ArgumentParser(description="Code cleanup")
    subparsers = parser.add_subparsers(dest="mode")
    for worker in workers:
        subparser = subparsers.add_parser(worker.id(), help=worker.help())
        worker.add_arguments(subparser)

    autocomplete(parser)
    args = vars(parser.parse_args())

    mode = TypeAdapter(str).validate_python(args["mode"])
    [worker] = [w for w in workers if w.id() == mode]
    worker.run(args)
