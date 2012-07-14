import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.md')).read()
CHANGES = open(os.path.join(here, 'CHANGES.md')).read()

requires = [
    'xtermcolor',
    ]

setup(name='git-rebranch',
      version='0.1',
      description='git-rebranch',
      long_description=README + '\n\n' +  CHANGES,
      classifiers=[
        "Programming Language :: Python",
        ],
      author='Dan Keder',
      author_email='dan.keder@gmail.com',
      url='',
      keywords='git rebranch rebase',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      scripts=[
        'bin/git-rebranch',
        ],
      )

# vim: expandtab
