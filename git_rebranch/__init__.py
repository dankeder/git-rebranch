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


def parse_args():
    parser = argparse.ArgumentParser("git-rebranch")

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--continue', action='store_true',
            help='continue interrupted rebranch',
            required=False, dest='cont')
    group.add_argument('--abort', action='store_true',
            help='abort interrupted rebranch',
            required=False)

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

    @property
    def branches(self):
        """ Return list of all branches mentioned in the config file.

        :return: List of branch names
        """
        result = []
        stack = [self.root]
        while stack:
            parent = stack.pop()
            for tree in parent.subtrees:
                result.append(tree.val)
                stack = [tree] + stack
        return result


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

    # Remember the current branch
    curbranch = git.current_branch

    try:
        # Check that all the required branches exist
        for branch in config.branches:
            git.get_sha1(branch)

        # Do rebranch
        _rebranch(git, curbranch, {}, config.rebase_plan(), args.dry_run)
    except GitError as e:
        error(e)
        sys.exit(1)

    # Checkout the original branch
    git.checkout(curbranch)


def do_rebranch_continue(args):
    git = Git()
    state = RebranchState(git.rootdir)

    if not state.in_progress():
        error("There is no rebranch in progress")
        sys.exit(1)

    # Continue the interrupted rebase
    if git.rebase_in_progress():
        info("Continue rebasing")
        (rc, stdout, stderr) = git.rebase_continue()
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        if rc != 0:
            error('Resolve the conflicts and run "git rebranch --continue"')
            error('To stop, run "git rebranch --abort"')
            sys.exit(1)

    # Continue rebasing
    try:
        (curbranch, orig_branches, plan) = state.load()
        _rebranch(git, curbranch, orig_branches, plan, args.dry_run)
    except GitError as e:
        error(e)
        sys.exit(1)


def do_rebranch_abort(args):
    git = Git()
    state = RebranchState(git.rootdir)

    if not state.in_progress():
        error("There is no rebranch in progress")
        sys.exit(1)

    # Abort an eventual rebase
    if git.rebase_in_progress():
        (rc, stdout, stderr) = git.rebase_abort()
        sys.stdout.write(stdout)
        sys.stderr.write(stderr)
        if rc != 0:
            error("Failed rebase --abort")

    # Just to be sure; check if the repo is clean
    if git.isdirty:
        error("Working copy is not clean")
        sys.exit(1)

    # Reset rebased branches to their original revisions
    (_, orig_branches, _) = state.load()
    for (branch, sha1) in orig_branches.items():
        info("Resetting {0} to {1}", branch, sha1)
        git.checkout(branch)
        git.reset_hard(sha1)

    state.clear()


def main():
    args = parse_args()

    if args.cont:
        # Continue an interrupted rebranch
        do_rebranch_continue(args)
    elif args.abort:
        # Abort an interrupted rebranch
        do_rebranch_abort(args)
    else:
        # Normal operation
        do_rebranch(args)




if __name__ == '__main__':
    main()

# vim: expandtab
