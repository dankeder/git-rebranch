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

import re
import os


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


class RebranchConfigError(Exception):
    def __init__(self, msg, line=None):
        self.msg = msg
        self.line = line


# vim: expandtab sw=4
