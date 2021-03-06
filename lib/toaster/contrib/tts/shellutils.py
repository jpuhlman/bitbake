#!/usr/bin/python

# ex:ts=4:sw=4:sts=4:et
# -*- tab-width: 4; c-basic-offset: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2015 Alexandru Damian for Intel Corp.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

# Utilities shared by tests and other common bits of code.

import sys, os, subprocess, fcntl, errno
import config
from config import logger


# License warning; this code is copied from the BitBake project, file bitbake/lib/bb/utils.py
# The code is originally licensed GPL-2.0, and we redistribute it under still GPL-2.0

# End of copy is marked with #ENDOFCOPY marker

def mkdirhier(directory):
    """Create a directory like 'mkdir -p', but does not complain if
    directory already exists like os.makedirs
    """

    try:
        os.makedirs(directory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise e

def lockfile(name, shared=False, retry=True):
    """
    Use the file fn as a lock file, return when the lock has been acquired.
    Returns a variable to pass to unlockfile().
    """
    config.logger.debug("take lockfile %s" % name)
    dirname = os.path.dirname(name)
    mkdirhier(dirname)

    if not os.access(dirname, os.W_OK):
        logger.error("Unable to acquire lock '%s', directory is not writable",
                     name)
        sys.exit(1)

    op = fcntl.LOCK_EX
    if shared:
        op = fcntl.LOCK_SH
    if not retry:
        op = op | fcntl.LOCK_NB

    while True:
        # If we leave the lockfiles lying around there is no problem
        # but we should clean up after ourselves. This gives potential
        # for races though. To work around this, when we acquire the lock
        # we check the file we locked was still the lock file on disk.
        # by comparing inode numbers. If they don't match or the lockfile
        # no longer exists, we start again.

        # This implementation is unfair since the last person to request the
        # lock is the most likely to win it.

        try:
            lf = open(name, 'a+')
            fileno = lf.fileno()
            fcntl.flock(fileno, op)
            statinfo = os.fstat(fileno)
            if os.path.exists(lf.name):
                statinfo2 = os.stat(lf.name)
                if statinfo.st_ino == statinfo2.st_ino:
                    return lf
            lf.close()
        except Exception:
            try:
                lf.close()
            except Exception:
                pass
            pass
        if not retry:
            return None

def unlockfile(lf):
    """
    Unlock a file locked using lockfile()
    """
    try:
        # If we had a shared lock, we need to promote to exclusive before
        # removing the lockfile. Attempt this, ignore failures.
        fcntl.flock(lf.fileno(), fcntl.LOCK_EX|fcntl.LOCK_NB)
        os.unlink(lf.name)
    except (IOError, OSError):
        pass
    fcntl.flock(lf.fileno(), fcntl.LOCK_UN)
    lf.close()

#ENDOFCOPY


def mk_lock_filename():
    our_name = os.path.basename(__file__)
    our_name = ".%s" % ".".join(reversed(our_name.split(".")))
    return config.LOCKFILE + our_name



class ShellCmdException(Exception):
    pass

def run_shell_cmd(command, cwd = None):
    if cwd is None:
        cwd = os.getcwd()

    config.logger.debug("_shellcmd: (%s) %s" % (cwd, command))
    p = subprocess.Popen(command, cwd = cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out,err) = p.communicate()
    p.wait()
    if p.returncode:
        if len(err) == 0:
            err = "command: %s \n%s" % (command, out)
        else:
            err = "command: %s \n%s" % (command, err)
        config.logger.warn("_shellcmd: error \n%s\n%s" % (out, err))
        raise ShellCmdException(err)
    else:
        #config.logger.debug("localhostbecontroller: shellcmd success\n%s" % out)
        return out

