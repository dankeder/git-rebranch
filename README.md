git-rebranch
============

The `git-rebranch` script is a git extension script for automating branch
rebasing. You describe the desired branch layout in a configuration file and
`git-rebranch` will take care of all the hard work when you run it.


Description
-----------

Ever happened to you that you worked on several features of your project at once
and you realized there is code shared in several features? Wouldn't it be nice
if changes to this shared code automagically appeared in all the branches that
depend on it?

The `git-rebranch` script allows you to describe the layout of your branches in
a file called `.gitrebranch` and rebase the branches according to this layout.

For example, let's say you have a branch called `master` and you are developing
new features in branches called `feature_1` and `feature_2`. You realize that
you need to make a changes to the library used in both feature branches. How do
you make the changes so that it's visible in both feature branches?  We have
several options here:

- Make the change manually in both branches. This is the most cumbersome and
  error-prone.

- Make a branch called `common` based on `master`. Put the shared commits
  into this branch and rebase the branches `feature_1` and `feature_2` onto
  this branch, like this:

        master
          |
          + common
              |
              +- feature_1
              |
              +- feature_2


  This is somewhat better that the previous apprach, but manually rebasing the
  branches when you add commit to the `common` or `master` branches is too much
  work. We can certainly do better.

- Describe the branch layout in the file called `.gitrebranch` in the repository
  directory and run `git rebranch` to automagically rebase the branches to match
  the specified layout. The format of the `.gitrebranch` file is described
  below, but for our example it would look like this:

        master
        	common
        		feature_1
        		feature_2

(Make sure that you use the 'Tab' characters to indent lines, not spaces.)

NOTE: The git-rebranch uses git-rebase internally. So make sure that you don't use
it to rebase any branches you already published. That would break other people's
history. But you certainly already know that :).


Format of the `.gitrebranch` file
---------------------------------

The `.gitrebranch` file must be stored in the repository root directory. Each
line starts with zero or more `Tab` characters, followed with a branch name. The
level of indentation represents the branch dependencies. In the following
example the branch `common` will be rebased upon `master` branch, whereas the
branches `feature_1` and `feature_2` will be rebased upon the `common` branch.
The branch `stable` is independent (i.e. it won't be rebased to anything).

    master
    	common
    		feature_1
    		feature_2
    stable


The file format is intentionally very simple so it's really easy to describe the
branch layout. Make sure that you use the `Tab` characters to indent lines,
otherwise it won't work.


Dry-run
-------

The script supports the "dry-run" operation that will only show what would be
done. You can use it to check whether the branch layout looks good:

    $ git rebranch --dry-run


Known Issues
------------

- If the rebasing fails because of a merge conlict, you have to resolve
  conflict and manually run `git rebase --continue`. Then run again `git
  rebranch` to rebase other branches.


Licence
-------

See the file LICENCE.


Author
------

- Dan Keder <<dan.keder@gmail.com>>
- <http://github.com/dankeder/git-rebranch>
