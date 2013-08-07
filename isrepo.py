#!/usr/bin/env python
#-*- coding:utf-8 -*-

"""Query the path defined by the first argument for being a git/svn repository.
Print the status/revision of the current repository.

Used for my custom prompt.

Most code courtesy of Stefan Majewsky.
"""

# code borrowed by S. Majewsky, tanks a lot!
#http://quickgit.kde.org/index.php?p=scratch%2Fmajewsky%2Fdevenv.git&a=blob&h=2405b0531653d9b833a785a135e68eaf658caebf&hb=841eb992e6c8adae5e831f6d43b8d5f373d15338&f=bin%2Fprettyprompt.py
# Link taken from his blog post at
# http://majewsky.wordpress.com/2011/09/13/a-clear-sign-of-madness/

import os.path as op
import sys
import subprocess as sp


def cat_file(fileName):
    """ Returns the content of the given file. No exception handling.
    """

    try:
        return "".join(open(fileName).readlines())
    except IOError:
        return ""


class NotARepoException(Exception):
    pass


def recognize_git_repo(path):
    """Returns a triple of repo path, path in repo, and repo status.
    E.g. ("/foo", "bar", "on branch master at 631d7a2") for
    path == "/foo/bar" and os.path.exists("/foo/.git").

    Throws NotARepoException if .git cannot be found.
    """

    base_path = op.realpath(path)
    sub_path = ""
    # find Git repo
    while not op.exists(op.join(base_path, ".git")):
        # ascend in directory hierarchy if possible
        base_path, new_sub_dir = op.split(base_path)
        sub_path = op.join(new_sub_dir, sub_path)
        # root directory reached? -> not in Git repo
        if new_sub_dir == "":
            raise NotARepoException

    # determine current branch and commit
    git_dir = op.join(base_path, ".git")
    head_ref = cat_file(op.join(git_dir, "HEAD")).strip()
    if head_ref.startswith("ref: refs/"):
        refSpec = head_ref[5:]
        head_ref2 = head_ref[10:]
        if head_ref2.startswith("heads/"):
            # current HEAD is a branch
            branch = head_ref2[6:]
        else:
            # current HEAD is a remote or tag -> include type specification
            branch = head_ref2
        branch_spec = branch
        # read corresponding file to find commit
        commit = cat_file(op.join(git_dir, refSpec)).strip()
        if commit == "" and op.exists(op.join(git_dir, "packed-refs")):
            packed_refs = open(op.join(git_dir, "packed-refs")).readlines()
            packed_refs = [ref.strip() for ref in packed_refs]
            for packed_ref in packed_refs:
                if packed_ref.endswith(refSpec):
                    commit = packed_ref[0:40]
                    break
    else:
        # current HEAD is detached
        branch_spec = "no branch"
        commit = head_ref

    if commit == "":  # before initial commit
        branch_spec = branch_spec + " before initial commit"
        extraInfo = "%s"%(branch_spec)
    else:
        extraInfo = "%s@%s"%(branch_spec, commit[0:6]) + git_is_dirty_string(path)

    return base_path, sub_path, extraInfo


def git_is_dirty_string(path):
    """Return '*' if the working directory is a dirty git repository, '' else.
    """

    try:
        proc = sp.Popen(["git", "diff-files", "--quiet"], cwd=path, stdout=sp.PIPE,
                        stderr=sp.PIPE)
    except OSError:
        result = ""
    else:
        proc.wait()
        result = "*" if proc.returncode == 1 else ""

    return result


def recognize_svn_repo(path):
    """Like recognize_git_repo, but for SVN repos. Repo status message looks like
    "on revision 42".

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

    return base_path, sub_path, "rev. %s"%revision


if(__name__ == '__main__'):
    try:  # is sys.argv[1] in a git repo?
        path, repopath, status = recognize_git_repo(sys.argv[1])
    except NotARepoException:
        try:  # test for svn
            path, repopath, status = recognize_svn_repo(sys.argv[1])
        except NotARepoException:
            status = ""

    # print prompt:
    if(len(status) > 0):
        print("["+ status + "] ")
    else:
        print("")
