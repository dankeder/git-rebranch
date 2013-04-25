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

import sys
import argparse
from xtermcolor.ColorMap import XTermColorMap

from gitrebranch.git import Git, GitError
from gitrebranch.config import RebranchConfig, RebranchConfigError
from gitrebranch.state import RebranchState


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

    # Remember the current branch
    curbranch = git.current_branch

    try:
        # Read .gitrebranch
        config = RebranchConfig(git)

        # Check that all the required branches exist
        for branch in config.branches:
            git.get_sha1(branch)

        # Do rebranch
        _rebranch(git, curbranch, {}, config.rebase_plan(), args.dry_run)
    except (GitError, RebranchConfigError) as e:
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

    # Checkout the original branch
    git.checkout(curbranch)


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
    (curbranch, orig_branches, _) = state.load()
    for (branch, sha1) in orig_branches.items():
        info("Resetting {0} to {1}", branch, sha1)
        git.checkout(branch)
        git.reset_hard(sha1)

    # Checkout the original branch
    git.checkout(curbranch)

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

# vim: expandtab sw=4
