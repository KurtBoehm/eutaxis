# This file is part of https://github.com/KurtBoehm/eutaxis.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re
from pathlib import Path
from typing import Final

_ssh_re: Final = re.compile(r"git@([^:]+):(.*)\.git")


def project_url(proj_path: Path):
    from git import Repo

    repo = Repo(proj_path)
    url = repo.remote().url
    if m := _ssh_re.fullmatch(url):
        base, repo = m.groups()
        url = f"https://{base}/{repo}"
    return url
