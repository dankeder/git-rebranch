git-rebranch
============

The `git-rebranch` script is a git extension script for easy branch rebasing.


Quickstart
----------

  1. Define the branch layout in the `.gitrebranch` file:

        master
            common
                feature_1
                feature_2

  2. Run `git rebranch`


Description
-----------

The `git-rebranch` is a git extension script for easy branch rebasing.

Let's say you have a branch called `master` and you are developing
new features in branches called `feature_1` and `feature_2`. You realize that
you need to make a changes to a file used in both feature branches. How do
you make the changes so they are visible in both feature branches?

Usually you make a branch called `common` which is based on `master`. Put the
common changes into this branch and rebase the branches `feature_1` and
`feature_2` onto `common`, so the branch layout looks like this:

        master
          +- common
              +- feature_1
              +- feature_2


However manually rebasing everything can be cumbersome and error-prone. We can
certainly do better.

The `git-rebranch` is designed to automate the rebasing. Just describe the
layout of your branches in a file called `.gitrebranch` in the git root
directory and run `git rebranch`.


Installation
------------

It is recommended to use a virtualenv python installation.

Install `git-rebranch`:

        $ python setup.py install


Format of `.gitrebranch`
------------------------

The file `.gitrebranch` must be stored in the repository root directory.

Each line starts with zero or more white-space characters (`tabs` or `spaces`),
followed with the name of the branch. The level of indentation is used to
determine the branch childs and parents.

In the following example the branch `common` will be rebased onto
`master`. Then the branches `feature_1` and `feature_2` will be
rebased onto `common`.

        master
            common
                feature_1
                feature_2


`git-rebranch` uses `git-rebase` internally. Make sure that you don't use it to
rebase any branches you already published because that would break other
people's history.


Options
-------

#### `--dry-run`

If you specify the `--dry-run` option `git-rebranch` will not perform any
changes, it will just show what would have been done. You can use it to check
whether the branch layout looks good:

    $ git rebranch --dry-run

#### `--continue`

If a conflict occurs during rebasing, you can resolve the conflict and then use
`git-rebranch --continue` to continue where it left off.

#### `--abort`

If a conflict occurs during rebasing and you don't want to resolve conflict, use
`git rebranch --abort` to abort the process. Everything that `git-rebranch` has
done so far will be reverted to the original state - even successfully rebased
branches will be reset to their original SHA1-s.


Licence
-------

GPLv2

Author
------

- Dan Keder (dan.keder@gmail.com)
- <http://github.com/dankeder/git-rebranch>
