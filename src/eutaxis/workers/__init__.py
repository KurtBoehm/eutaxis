# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from .cpp import CppWorker
from .meson import MesonWorker
from .python import PythonWorker
from .worker import Worker

workers: list[type[Worker]] = [CppWorker, MesonWorker, PythonWorker]
