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
import sys

from setuptools import setup, find_packages
from subprocess import Popen, PIPE

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.md')).read()


def get_version():
    """
    Get version from PKG-INFO file.
    """
    try:
        # Try to get version from the PKG-INFO file
        f = open('PKG-INFO', 'r')
        for line in f.readlines():
            if line.startswith('Version: '):
                return line.split(' ')[1].strip()
    except IOError:
        # Try to get the version from the latest git tag
        p = Popen(['git', 'describe', '--tags'], stdout=PIPE, stderr=PIPE)
        p.stderr.close()
        lines = p.stdout.readlines()
        try:
            return lines[0].strip()
        except IndexError:
            sys.stderr.write('Cannot determine version. Try running "git fetch --tags" first.\n')
            sys.exit(1)


requires = [
    'xtermcolor',
    ]

setup(name='git-rebranch',
        version=get_version(),
        description='git-rebranch',
        long_description=README + '\n\n' +  CHANGES,
        classifiers=[
                "Programming Language :: Python",
            ],
        author='Dan Keder',
        author_email='dan.keder@gmail.com',
        url='http://github.com/dankeder/git-rebranch',
        keywords='git rebranch rebase',
        packages=find_packages(),
        include_package_data=True,
        zip_safe=False,
        install_requires=requires,
        entry_points={
                'console_scripts': [ 'git-rebranch = gitrebranch:main' ]
            }
    )

# vim: expandtab
