# Copyright (C) 2012  Dan Keder <dan.keder@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import pickle


class RebranchState(object):
    def __init__(self, gitroot):
        self._statefile = os.path.join(gitroot, '.git', 'REBRANCH_STATE')

    def store(self, curbranch, orig_branches, plan):
        with open(self._statefile, 'w') as fh:
            pickle.dump((curbranch, orig_branches, plan), fh)

    def load(self):
        with open(self._statefile, 'r') as fh:
            return pickle.load(fh)

    def clear(self):
        os.unlink(self._statefile)

    def in_progress(self):
        return os.path.exists(self._statefile)


# vim: expandtab sw=4
