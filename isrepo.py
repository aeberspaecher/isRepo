#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""Query the path defined by the first argument for being a git/svn repository.
Print the status/revision of the current repository.

Used for my custom prompt.
"""

# SVN code and original git code borrowed from S. Majewsky, tanks a lot!
#http://quickgit.kde.org/index.php?p=scratch%2Fmajewsky%2Fdevenv.git&a=blob&h=2405b0531653d9b833a785a135e68eaf658caebf&hb=841eb992e6c8adae5e831f6d43b8d5f373d15338&f=bin%2Fprettyprompt.py
# Link taken from his blog post at
# http://majewsky.wordpress.com/2011/09/13/a-clear-sign-of-madness/

import os
import os.path as op
import sys
import subprocess as sp


SHA1_length = 5  # print this many characters of SHA1 strings
dirty_appendix = "*"
at_character = "@"  # connect branch and commit with this character, e.g. master@e7123


def cat_file(file_name):
    """ Returns the content of the given file. No real exception handling.
    """

    try:
        return "".join(open(file_name).readlines())
    except IOError:
        return ""


class NotARepoException(Exception):
    """Raised if path is not part of a repository.
    """

    pass


class GitFailure(Exception):
    """Raised if a command fails.
    """
    pass


def recognize_git_repo(path):
    """Returns a triple of repo path, path in repo, and repo status. E.g.
    ("/foo", "bar", "on branch master at 631d7a2") for path == "/foo/bar" and
    os.path.exists("/foo/.git").

    Throws NotARepoException if .git cannot be found.
    """

    # TODO: alternative to directory traversal in repo recovery: check git exit status.
    # 128 means something went wrong. to checkout: which other causes may lead to 128?

    base_path = op.realpath(path)
    sub_path = ""
    # find git repo (resides in a .git directory):
    while not op.exists(op.join(base_path, ".git")):
        # ascend in directory hierarchy if possible:
        base_path, new_sub_dir = op.split(base_path)
        sub_path = op.join(new_sub_dir, sub_path)
        # root directory reached? -> not in git repo
        if new_sub_dir == "":
            raise NotARepoException

    # determine current branch and commit, use git commands:
    # get commit that HEAD points to: git rev-parse --verify HEAD
    # find branch: git rev-parse --symbolic-full-name --abbrev-ref HEAD
    branch = get_git_branch(path)

    try:
        commit = get_git_commit(path)[:SHA1_length]
    except GitFailure:  # TODO: can there be other exceptions raised?
        commit = "before initial commit"

    is_dirty_appendix = get_git_dirty_string(path, dirty_appendix)

    status = branch + at_character + commit + is_dirty_appendix

    return base_path, sub_path, status


def get_git_branch(path):
    """Find branch for the git repository in path.
    """

    try:
        branch = sp.check_output(["git", "symbolic-ref", "HEAD"],
                                 universal_newlines=True, cwd=path, shell=False,
                                 stderr=sp.STDOUT)
    except sp.CalledProcessError:
        # interpret git returning an error exit code as not being on a branch:
        raise GitFailure

    return branch.replace("\n", "").split("/")[-1]


def get_git_commit(path):
    """Find git commit for repository in path.
    """

    try:
        commit = sp.check_output(["git", "rev-parse", "--verify", "HEAD"],
                                 universal_newlines=True, cwd=path, shell=False,
                                 stderr=sp.STDOUT)
    except sp.CalledProcessError:
        raise GitFailure

    return commit.replace("\n", "")


def get_git_dirty_string(path, dirty_appendix="*"):
    """Return a specified character if the working directory is a 'dirty' git
    repository, '' else.
    """

    try:
        proc = sp.Popen(["git", "diff-files", "--quiet"], cwd=path, stdout=sp.PIPE,
                        stderr=sp.PIPE)
    except OSError:
        result = ""
    else:
        proc.wait()
        result = dirty_appendix if proc.returncode == 1 else ""

    return result


def recognize_svn_repo(path):
    """Like recognize_git_repo, but for SVN repos. Repo status message looks
    like "on revision 42".

    Throws NotARepoException if .svn cannot be found.
    """

    base_path = op.realpath(path)
    sub_path = ""
    # find SVN repo
    if not op.exists(op.join(base_path, ".svn")):
        raise NotARepoException
    while op.exists(op.join(op.dirname(base_path), ".svn")):
        # ascend in directory hierarchy as far as possible
        base_path, new_sub_dir = op.split(base_path)
        sub_path = op.join(new_sub_dir, sub_path)

    # ask `svn info` for revision
    svn_info_output = sp.Popen(["svn", "info"], cwd=path,
                               stdout=sp.PIPE).communicate()[0]
    for line in svn_info_output.splitlines():
        if line.startswith("Revision: "):
            revision = line[10:]
    rev_string = "rev. {}".format(revision)

    return base_path, sub_path, rev_string


if __name__ == '__main__':

    # reopen stdout for writing with immediate flushing
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)

    try:  # is sys.argv[1] in a git repo?
        path, repopath, status = recognize_git_repo(sys.argv[1])
    except NotARepoException:
        try:  # test sys.argv[1] for being a svn repo
            path, repopath, status = recognize_svn_repo(sys.argv[1])
        except NotARepoException:
            status = ""

    # print prompt:
    if len(status) > 0:
        print("["+ status + "] ")
    else:
        print(status)

    os._exit(0)  # quit without garbage collection
