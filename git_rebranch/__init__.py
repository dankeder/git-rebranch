import re
import os.path
import sys
import argparse
import pickle
from xtermcolor.ColorMap import XTermColorMap

from git_rebranch.git import Git, GitError

cmap = XTermColorMap()


def info(msg, *args):
    msg = msg.format(*args)
    sys.stdout.write(cmap.colorize("{0}\n".format(msg), 0x00ff00))


def error(msg):
    sys.stderr.write(cmap.colorize("{0}\n".format(msg), 0xff0000))


def parse_cmdline():
    parser = argparse.ArgumentParser("git-rebranch")
    parser.add_argument('--dry-run', action='store_true',
            help='dry-run operation')
    parser.add_argument('--verbose', '-v', action='store_true',
            help='verbose operation')

    args = parser.parse_args()

    return args


class RebranchConfigError(Exception):
    def __init__(self, msg, line=None):
        self.msg = msg
        self.line = line


class RebranchConfig(object):
    class _Tree(object):
        def __init__(self, val):
            self.val = val
            self.subtrees = []

        def to_str(self, level):
            s = ''
            if self.val is not None:
                s = "{0}\n".format(self.val)
            for node in self.subtrees:
                s += (" " * 4 * level) + node.to_str(level+1)
            return s

        def add_subtree(self, tree):
            self.subtrees.append(tree)

    def __init__(self, git):
        configfile = os.path.join(git.rootdir, ".gitrebranch")
        with open(configfile, 'r') as fh:
            self.read(fh)

    def read(self, fileobj):
        self._fileobj = fileobj

        stack = [RebranchConfig._Tree(None)]
        last = stack[0]
        for (lineno, level, branchname) in self._parselines():
            tree = RebranchConfig._Tree(branchname)

            if level == len(stack) - 1:    # on the same level
                stack[-1].add_subtree(tree)
                last = tree

            elif level == len(stack):      # on the +1 level
                last.add_subtree(tree)
                stack.append(last)
                last = tree

            elif level < len(stack) - 1:   # on the -n level
                stack = stack[:level+1]
                stack[-1].add_subtree(tree)
                last = tree

            else:
                raise RebranchConfigError("Bad indentation", lineno)

        self.root = stack[0]

    def _parselines(self):
        indentwidth = None;
        lineno = 0
        for line in self._fileobj.readlines():
            lineno += 1
            line = line.rstrip()
            if line == '': next

            match = re.match("([\t ]*)(.+)", line)
            if match is None:
                raise RebranchConfigError("Malformed config file format",
                        lineno)
            indent = len(match.group(1))
            branchname = match.group(2)

            # We guess the indent width from the first indented line found. The
            # indent width of all the following lines must be multiple of it.
            if indent:
                if indentwidth is None:
                    indentwidth = indent
                if indent % indentwidth != 0:
                    raise RebranchConfigError("Wrong indentation",
                            lineno)
                level = indent / indentwidth
            else:
                level = 0
            yield (lineno, level, branchname)

    def to_str(self):
        return self.root.to_str(0)


    def rebase_plan(self):
        """ Create a rebasing plan.

        :return: List of rebasing instructions
        """
        plan = []
        stack = [self.root]
        while stack:
            parent = stack.pop()
            for tree in parent.subtrees:
                parentbranch = parent.val
                childbranch = tree.val
                plan.append((parentbranch, childbranch))
                stack = [tree] + stack
        return plan


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


def _rebranch(git, curbranch, orig_branches, plan, dry_run):
    state = RebranchState(git.rootdir)
    while plan:
        (parentbranch, childbranch) = plan[0]
        plan = plan[1:]
        orig_branches[childbranch] = git.get_sha1(childbranch)

        state.store(curbranch, orig_branches, plan)

        if parentbranch is not None:
            info("Rebasing {0} onto {1}", childbranch, parentbranch)

            # Check if we are in the middle of a rebase?
            if git.rebase_in_progress():
                error("Rebase in progress")
                sys.exit(1)

            # Rebase commit range 'orig_branches[parentbranch]..childbranch' onto
            # the (new) parentbranch
            if not dry_run:
                (rc, stdout, stderr) = git.rebase(parentbranch, orig_branches[parentbranch], childbranch)
                sys.stdout.write(stdout)
                sys.stderr.write(stderr)
                if rc != 0:
                    error('Rebranching failed.')
                    error('To continue, resolve conflicts and run "git rebranch --continue"')
                    error('To stop rebasing and return everything as it were, run "git rebranch --abort"')
                    sys.exit(1)

    state.clear()


def do_rebranch(args):
    git = Git()
    state = RebranchState(git.rootdir)

    # Check if we were interrupted
    if state.in_progress():
        error("Rebranch is in progress. Use --continue or --abort")
        sys.exit(1)

    # Check if the repo is clean
    if git.isdirty:
        error("Working copy is not clean, aborting.")
        sys.exit(1)

    # Read .gitrebranch
    config = RebranchConfig(git)

    # TODO: Check that all the required branches exist

    # Remember the current branch
    curbranch = git.current_branch

    # Do rebranch
    try:
        _rebranch(git, curbranch, {}, config.rebase_plan(), args.dry_run)
    except GitError as e:
        error(e)
        sys.exit(1)

    # Checkout the original branch
    git.checkout(curbranch)


if __name__ == '__main__':
    args = parse_cmdline()
    cmap = XTermColorMap()
    git = Git(args.verbose, args.dry_run)

    # Get config file path
    try:
        config_file = os.path.join(git.root(), ".gitrebranch")
        fh = open(config_file, 'r')
        config = Config(fh)
    except IOError:
        error("Failed opening file {0}".format(config_file))
        sys.exit(1)

    if (args.dry_run):
        sys.stdout.write(str(config))
        sys.exit(0)
    else:
        try:
            # Remember the current branch
            current_branch = git.current_branch()

            # Rebranch
            for tree in config.trees():
                git.rebranch(tree)

            # Checkout the original branch
            git.checkout(current_branch)
        except Exception, e:
            error(e)
            sys.exit(1)


# vim: expandtab
