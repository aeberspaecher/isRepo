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


def catFile(fileName):
    """ Returns the content of the given file. No exception handling.
    """

    try:
        return "".join(open(fileName).readlines())
    except IOError:
        return ""


class NotARepoException(Exception):
    pass


def recognizeGitRepo(path):
    """Returns a triple of repo path, path in repo, and repo status.
    E.g. ("/foo", "bar", "on branch master at 631d7a2") for
    path == "/foo/bar" and os.path.exists("/foo/.git").

    Throws NotARepoException if .git cannot be found.
    """

    basePath = op.realpath(path)
    subPath = ""
    # find Git repo
    while not op.exists(op.join(basePath, ".git")):
        # ascend in directory hierarchy if possible
        basePath, newSubDir = op.split(basePath)
        subPath = op.join(newSubDir, subPath)
        # root directory reached? -> not in Git repo
        if newSubDir == "":
            raise NotARepoException

    # determine current branch and commit
    gitDir = op.join(basePath, ".git")
    headRef = catFile(op.join(gitDir, "HEAD")).strip()
    if headRef.startswith("ref: refs/"):
        refSpec = headRef[5:]
        headRef2 = headRef[10:]
        if headRef2.startswith("heads/"):
            # current HEAD is a branch
            branch = headRef2[6:]
        else:
            # current HEAD is a remote or tag -> include type specification
            branch = headRef2
        branchSpec = branch
        # read corresponding file to find commit
        commit = catFile(op.join(gitDir, refSpec)).strip()
        if commit == "" and op.exists(op.join(gitDir, "packed-refs")):
            packedRefs = open(op.join(gitDir, "packed-refs")).readlines()
            packedRefs = map(str.strip, packedRefs)
            for packedRef in packedRefs:
                if packedRef.endswith(refSpec):
                    commit = packedRef[0:40]
                    break
    else:
        # current HEAD is detached
        branchSpec = "no branch"
        commit = headRef

    if commit == "":  # before initial commit
        branchSpec = branchSpec + " before initial commit"
        extraInfo = "%s"%(branchSpec)
    else:
        extraInfo = "%s@%s"%(branchSpec, commit[0:6]) + GitIsDirtyString(path)

    return basePath, subPath, extraInfo


def GitIsDirtyString(path):
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


def recognizeSvnRepo(path):
    """Like recognizeGitRepo, but for SVN repos. Repo status message looks like
    "on revision 42".

    Throws NotARepoException if .svn cannot be found.
    """
    basePath = op.realpath(path)
    subPath = ""
    # find SVN repo
    if not op.exists(op.join(basePath, ".svn")):
        raise NotARepoException
    while op.exists(op.join(op.dirname(basePath), ".svn")):
        # ascend in directory hierarchy as far as possible
        basePath, newSubDir = op.split(basePath)
        subPath = op.join(newSubDir, subPath)

    # ask `svn info` for revision
    svnInfoOutput = sp.Popen(["svn", "info"], cwd=path,
                             stdout=sp.PIPE).communicate()[0]
    for line in svnInfoOutput.splitlines():
        if line.startswith("Revision: "):
            revision = line[10:]

    return basePath, subPath, "rev. %s" % revision

if(__name__ == '__main__'):
    try:  # is sys.argv[1] in a git repo?
        path, repopath, status = recognizeGitRepo(sys.argv[1])
    except:
        try:  # test for svn
            path, repopath, status = recognizeSvnRepo(sys.argv[1])
        except:
            status = ""

    if(len(status) > 0):
        print("["+ status + "] ")
    else:
        print("")
