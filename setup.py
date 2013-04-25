import os

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
        line = p.stdout.readlines()[0]
        return line.strip()


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
                'console_scripts': [ 'git-rebranch = git_rebranch:main' ]
            }
    )

# vim: expandtab
