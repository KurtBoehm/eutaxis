# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Final, Literal

mpl_2_0 = """\
{0} This Source Code Form is subject to the terms of the Mozilla Public
{0} License, v. 2.0. If a copy of the MPL was not distributed with this
{0} file, You can obtain one at https://mozilla.org/MPL/2.0/.
"""

License = Literal["MPL-2.0"]

_licenses: Final[dict[License, str]] = {"MPL-2.0": mpl_2_0}


def license_header(license: License, comment_begin: str):
    return _licenses[license].format(comment_begin)
