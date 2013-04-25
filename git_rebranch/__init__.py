#!/usr/bin/python

import re
import os.path
import sys
import argparse
from xtermcolor.ColorMap import XTermColorMap

from git_rebranch.git import Git, GitError

def parse_cmdline():
    parser = argparse.ArgumentParser("git-rebranch")
    parser.add_argument('--dry-run', action='store_true',
            help='dry-run operation')
    parser.add_argument('--verbose', '-v', action='store_true',
            help='verbose operation')

    args = parser.parse_args()

    return args



class Config(object):
    class Node(object):
        def __init__(self, branch, flags=[]):
            self.branch = branch
            self.flags = flags
            self.subtrees = []

        def to_str(self, level):
            if len(self.flags):
                s = "{0}  [%s]\n".format(self.branch, " ".join(self.flags))
            else:
                s = "{0}\n".format(self.branch)
            if len(self.subtrees):
                for node in self.subtrees:
                    s += (" " * 4 * level) + node.to_str(level+1)
            return s

        def add_tree(self, tree):
            self.subtrees.append(tree)


    def __init__(self, fd):
        root = Config.Node('_root')
        self.tree = self._parse_tree(fd)

    def trees(self):
        return self.tree.subtrees

    def _parse_tree(self, fd):
        stack = [Config.Node('_root_')]
        last = stack[0]
        for (indent, branch, flags) in self._parse_lines(fd):
            node = Config.Node(branch, flags)

            if indent == len(stack) - 1:    # same level
                stack[-1].add_tree(node)
                last = node

            elif indent == len(stack):      # +1 level
                last.add_tree(node)
                stack.append(last)
                last = node

            elif indent < len(stack) - 1:   # -n level
                stack = stack[:indent+1]
                stack[-1].add_tree(node)
                last = node

            else:
                # Bad indentation
                raise Exception("Bad indentation")

        return stack[0]

    def _parse_lines(self, fd):
        indentwidth = None;
        for line in fd.readlines():
            line = line.rstrip()
            if line == '':
                next

            match = re.match("([\t ]*)(.+)( \[(.*)\])?\s*", line)
            if match is None:
                raise Exception("Malformed config file format")
            indent = len(match.group(1))
            branch = match.group(2)
            flags = match.group(4)

            # We guess the indent width from the first indented line found. The
            # indent of all the following lines must be multiple of the guessed
            # indent width.
            if indent > 0:
                if indentwidth is None:
                    indentwidth = indent
                if indent % indentwidth != 0:
                    raise Exception("Malformed config file: indent")
                indent /= indentwidth

            branch = branch.strip()

            if flags is not None:
                flags = flags.split(',')
            else:
                flags = []

            yield (indent, branch, flags)

    def __str__(self):
        s = ""
        for tree in self.tree.subtrees:
            s += tree.to_str(1)
        return s

def error(msg):
    sys.stderr.write(cmap.colorize("Error: {0}\n".format(msg), 0xff0000))

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
