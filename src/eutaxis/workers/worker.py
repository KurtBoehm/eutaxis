# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from abc import ABC, abstractmethod
from argparse import ArgumentParser
from typing import Any


class Worker(ABC):
    @staticmethod
    @abstractmethod
    def id() -> str: ...

    @staticmethod
    @abstractmethod
    def help() -> str: ...

    @staticmethod
    @abstractmethod
    def add_arguments(parser: ArgumentParser) -> None: ...

    @staticmethod
    @abstractmethod
    def run(raw_args: dict[str, Any]) -> None: ...
