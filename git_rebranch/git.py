import sys
import os
from subprocess import Popen, PIPE

class GitError(Exception):
    def __init__(self, msg, stderr=None):
        self.msg = msg
        self.stderr = stderr

    def __str__(self):
        return self.msg

class Git(object):
    """ This class allows running git commands.
    """

    def __init__(self):
        pass

    @property
    def rootdir(self):
        """ Get the root directory of the git repo.

        :return: Root path to the git repository.
        """
        process = self._run('rev-parse', '--show-toplevel')
        if process.returncode != 0:
            raise GitError("Failed getting git root directory",
                process.stderr.read())
        return process.stdout.readline().strip()

    @property
    def current_branch(self):
        """ Get the current branch name. If the repo is in detached state return
        None.
        
        :return: Current branch name or None.
        """
        process = self._run('branch')
        if process.returncode != 0:
            raise GitError("Failed getting current branch")
        for line in process.stdout.readlines():
            line = line.strip()
            if line.startswith('*'):
                branch = line[2:]
                if branch == '(no branch)':
                    return None
                else:
                    return branch

    @property
    def isdirty(self):
        """ Get the repository status - i.e. check if there any uncommited
        changes.

        :return: True if the repository is dirty, False otherwise.
        """
        process = self._run('status', '--porcelain')
        if process.returncode != 0:
            raise GitError("Git status failed",
                process.stderr.read())
        for line in process.stdout.readlines():
            if not line.startswith('??'):
                return True
        return False

    def checkout(self, branch):
        """ Checkout a branch.

        :param: branch: Branch to checkout
        """
        process = self._run('checkout', branch)
        if process.returncode != 0:
            raise GitError("Checkout of branch {0} failed".format(branch),
                    process.stderr.read())

    def get_sha1(self, rev):
        """ Get the SHA1 hash of the specified revision.

        :param: rev: Branch name
        :return: SHA1 of the specified revision
        """
        process = self._run('rev-parse', '--short', rev)
        if process.returncode != 0:
            raise GitError("Failed getting SHA1 hash of '{0}'".format(rev))
        sha1 = process.stdout.readline().strip()
        return sha1

    def reset_hard(self, rev):
        """ Perform a "git reset --hard rev".

        :param: rev: Target revision
        """
        process = self._run('reset', '--hard', rev)
        if process.returncode != 0:
            raise GitError("Failed resetting HEAD to {0}".format(rev))

    def rebase_abort(self):
        """ Perform a "git rebase --abort".
        """
        process = self._run('rebase', '--abort')
        process.wait()

        return (process.returncode, process.stdout.read(), process.stderr.read())

    def rebase_continue(self):
        """ Perform a "git rebase --continue".
        """
        process = self._run('rebase', '--continue')
        process.wait()

        return (process.returncode, process.stdout.read(), process.stderr.read())

    def rebase_in_progress(self):
        """ Return True if the repository is in the middle of a rebase
        operation.
        """
        return os.path.exists(os.path.join(self.rootdir, '.git', 'rebase-merge'))

    def rebase(self, newbase, startrev, endrev):
        """ Rebase the commits between the startrev and endrev onto newbase.

        :param: newbase: Commits onto this revision
        :param: startrev: Start revision
        :param: endrev: End revision
        :return: Tuple containing the return code, stdout and stderr output of
        the git rebase command
        """
        orig_end_sha1 = self.get_sha1(endrev)
        process = self._run('rebase', '--merge', '--onto', newbase,
                startrev, endrev)
        process.wait()

        return (process.returncode, process.stdout.read(), process.stderr.read())

    def _run(self, *args):
        """ Run the 'git' command with the specified arguments and return the
            process object.
        """
        cmd = ['git'] + list(args)
        process = Popen(cmd, stdout=PIPE, stderr=PIPE)
        process.wait()
        return process
