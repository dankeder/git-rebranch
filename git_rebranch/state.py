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
