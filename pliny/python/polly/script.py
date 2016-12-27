#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
#

from __future__ import print_function

import atexit
import codecs
import fnmatch
import getpass
import os
import shutil
import subprocess
import sys
import tempfile

# The notion here is to use the global function namespace for common
# script operations.  They fall into a few patterns:
# 
# - split and join are path operations
#
# - "path" param means path to a file 
# - "dir" param means path to a directory
# - "name" param means the file or directory name without any
#   preceding path
# - "pattern" param means a shell glob, a la "*.py"
#
# - read_, write_, append_, and touch_entry are for stashing named
#   values in the a temporary location in the filesystem, to make it
#   easy to use those values when you invoke an external command
#
# - If the function involves creating a file or directory, it may well
#   return the path

def error(message, *args):
    _print("Error", message, args, sys.stderr)

    raise Exception()

def warn(message, *args):
    _print("Warn", message, args, sys.stderr)

def notice(message, *args):
    _print(None, message, args, sys.stdout)

def debug(message, *args):
    pass

def _print(category, message, args, file):
    if category:
        message = "{}: {}".format(category, message)

    if args:
        message = message.format(*args)

    script = split(sys.argv[0])[1]
    message = "{}: {}".format(script, message)

    print(message, file=file)

join = os.path.join
split = os.path.split
exists = os.path.exists
is_dir = os.path.isdir
is_file = os.path.isfile
exit = sys.exit

def read(path):
    with codecs.open(path, encoding="utf-8", mode="r") as file:
        return file.read()

def write(path, string):
    with codecs.open(path, encoding="utf-8", mode="w") as file:
        file.write(string)

    return path

def append(path, string):
    with codecs.open(path, encoding="utf-8", mode="a") as file:
        file.write(string)

    return path

def prepend(path, string):
    orig = read(path)
    prepended = string + orig
    write(path, prepended)

    return path

def touch(path):
    return append(path, "")

_entry_dir = tempfile.mkdtemp()

def _remove_entry_dir():
    remove(_entry_dir)

atexit.register(_remove_entry_dir)

def read_entry(key):
    return read(join(_entry_dir, key))

def write_entry(key, string):
    path = get_entry_path(key)
    write(path, string)
    return path

def append_entry(key, string):
    path = get_entry_path(key)
    append(path, string)
    return path

def touch_entry(key):
    return append_entry(key, "")

def get_entry_path(key):
    return join(_entry_dir, key)

def copy(from_path, to_path):
    to_dir = split(to_path)[0]

    if to_dir:
        make_dirs(to_dir)

    if is_dir(from_path):
        _copytree(from_path, to_path)
    else:
        shutil.copy(from_path, to_path)

move = shutil.move

def remove(path):
    if not exists(path):
        return

    if is_dir(path):
        shutil.rmtree(path, ignore_errors=True)
    else:
        os.remove(path)

def find(dir, *patterns):
    matched_paths = set()

    if not patterns:
        patterns = ("*",)

    for root, dirs, files in os.walk(dir):
        for pattern in patterns:
            matched_dirs = fnmatch.filter(dirs, pattern)
            matched_files = fnmatch.filter(files, pattern)

            matched_paths.update([join(root, x) for x in matched_dirs])
            matched_paths.update([join(root, x) for x in matched_files])

    return sorted(matched_paths)

# Returns the current working directory so you can change it back
def change_dir(dir):
    notice("Changing directory to '{}'", dir)

    cwd = os.getcwd()
    os.chdir(dir)
    return cwd

def list_dir(dir, *patterns):
    names = os.listdir(dir)

    if not patterns:
        return sorted(names)

    matched_names = set()

    for pattern in patterns:
        matched_names.update(fnmatch.filter(names, pattern))

    return sorted(matched_names)

def make_dirs(dir):
    if not exists(dir):
        os.makedirs(dir)

    return dir

def make_temp_dir():
    return tempfile.mkdtemp()

def make_user_temp_dir():
    temp_dir = tempfile.gettempdir()
    user = getpass.getuser()
    user_temp_dir = join(temp_dir, user)

    return make_dirs(user_temp_dir)

def call(command, *args):
    if args:
        command = command.format(*args)

    notice("Calling '{}'", command)

    subprocess.check_call(command, shell=True)

def make_archive(input_dir, output_dir, output_name, format="gztar"):
    temp_dir = make_temp_dir()
    temp_input_dir = join(temp_dir, output_name)

    copy(input_dir, temp_input_dir)

    base_output_path = join(output_dir, output_name)

    return shutil.make_archive(base_name=base_output_path,
                               format=format,
                               root_dir=temp_dir,
                               base_dir=output_name)

# Modified copytree impl that allows for already existing destination
# dirs
def _copytree(src, dst, symlinks=False, ignore=None):
    """Recursively copy a directory tree using copy2().

    If exception(s) occur, an Error is raised with a list of reasons.

    If the optional symlinks flag is true, symbolic links in the
    source tree result in symbolic links in the destination tree; if
    it is false, the contents of the files pointed to by symbolic
    links are copied.

    The optional ignore argument is a callable. If given, it
    is called with the `src` parameter, which is the directory
    being visited by copytree(), and `names` which is the list of
    `src` contents, as returned by os.listdir():

        callable(src, names) -> ignored_names

    Since copytree() is called recursively, the callable will be
    called once for each directory that is copied. It returns a
    list of names relative to the `src` directory that should
    not be copied.

    XXX Consider this example code rather than the ultimate tool.

    """
    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not exists(dst):
        os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                _copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                shutil.copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except shutil.Error, err:
            errors.extend(err.args[0])
        except EnvironmentError, why:
            errors.append((srcname, dstname, str(why)))
    try:
        shutil.copystat(src, dst)
    except OSError, why:
        if shutil.WindowsError is not None and isinstance(why, shutil.WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise shutil.Error, errors
