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

import atexit as _atexit
import codecs as _codecs
import fnmatch as _fnmatch
import getpass as _getpass
import os as _os
import random as _random
import re as _re
import shutil as _shutil
import subprocess as _subprocess
import sys as _sys
import tarfile as _tarfile
import tempfile as _tempfile
import traceback as _traceback

# The notion here is to use the global function namespace for common
# script operations.  They fall into a few patterns:
# 
# - split and join are path operations
#
# - "path" param means path to a file or direcotry
# - "dir" param means path to a directory
# - "file" param means path to a file
# - "name" param means the file or directory name without any
#   preceding path
# - "pattern" param means a shell glob, a la "*.py"
# - "expr" param means a regular expression
# - "command" param means something we pass to the shell
#
# - read_, write_, append_, and touch_entry are for stashing named
#   values in the a temporary location in the filesystem, to make it
#   easy to use those values when you invoke an external command
#
# - If the function involves creating a file or directory, it may
#   return the path
#
# - Don't fuss, just do it
#
# - Don't be shy about talking about what you're doing on the console
# 
# Groups:
#
# - Logging: fail, error, warn, notice, debug, exit

def fail(message, *args):
    error(message, *args)

    if isinstance(message, BaseException):
        raise message

    raise Exception(message)

def error(message, *args):
    _traceback.print_exc()
    _print_message("Error", message, args, _sys.stderr)

def warn(message, *args):
    _print_message("Warn", message, args, _sys.stderr)

def notice(message, *args):
    _print_message(None, message, args, _sys.stdout)

def debug(message, *args):
    _print_message("Debug", message, args, _sys.stdout)

def exit(message=None, *args):
    if message is None:
        _sys.exit()

    message_args = args[1:]

    _print_message("Error", message, message_args, _sys.stderr)

    _sys.exit(1)

def _print_message(category, message, args, file):
    message = _format_message(category, message, args)

    print(message, file=file)
    file.flush()

def _format_message(category, message, args):
    if isinstance(message, BaseException):
        message = str(message)

    if category:
        message = "{}: {}".format(category, message)

    if args:
        message = message.format(*args)

    script = split(_sys.argv[0])[1]
    message = "{}: {}".format(script, message)

    return message

absolute_path = _os.path.abspath
normalize_path = _os.path.normpath
exists = _os.path.exists
is_absolute = _os.path.isabs
is_dir = _os.path.isdir
is_file = _os.path.isfile
is_link = _os.path.islink

join = _os.path.join
split = _os.path.split
split_ext = _os.path.splitext

LINE_SEP = _os.linesep
PATH_SEP = _os.sep
ENV = _os.environ

current_dir = _os.getcwd

def parent_dir(path):
    path = normalize_path(path)
    parent, child = split(path)

    return parent

def file_name(file):
    file = normalize_path(file)
    dir, name = split(file)

    return name

def file_stem(file):
    name = file_name(file)

    if name.endswith(".tar.gz"):
        name = name[:-3]

    stem, ext = split_ext(name)

    return stem

def file_ext(file):
    name = file_name(file)
    stem, ext = split_ext(name)
    
    return ext

def read(file):
    with _codecs.open(file, encoding="utf-8", mode="r") as f:
        return f.read()

def write(file, string):
    with _codecs.open(file, encoding="utf-8", mode="w") as f:
        f.write(string)

def append(file, string):
    with _codecs.open(file, encoding="utf-8", mode="a") as f:
        f.write(string)

def prepend(file, string):
    orig = read(file)
    prepended = string + orig
    write(file, prepended)

def touch(file):
    return append(file, "")

def read_lines(file):
    with _codecs.open(file, encoding="utf-8", mode="r") as f:
        return f.readlines()

def write_lines(file, lines):
    with _codecs.open(file, encoding="utf-8", mode="r") as f:
        return f.writelines(lines)

def append_lines(file, lines):
    with _codecs.open(file, encoding="utf-8", mode="a") as f:
        f.writelines(string)

def prepend_lines(file, lines):
    orig_lines = read_lines(file)

    with _codecs.open(file, encoding="utf-8", mode="w") as f:
        f.writelines(lines)
        f.writelines(orig_lines)

_temp_dir = _tempfile.mkdtemp(prefix="plano.")

def _get_temp_file(key):
    assert not key.startswith("_")

    return join(_temp_dir, "file", key)

def _remove_temp_dir():
    remove(_temp_dir)

_atexit.register(_remove_temp_dir)

def read_temp(key):
    file = _get_temp_file(key)
    return read(file)

def write_temp(key, string):
    file = _get_temp_file(key)
    write(file, string)
    return file

def append_temp(key, string):
    file = _get_temp_file(key)
    append(file, string)
    return file

def make_temp(key):
    return append_temp(key, "")

def open_temp(key, mode="r"):
    file = _get_temp_file(key)

    return _codecs.open(file, encoding="utf-8", mode=mode)

# This one is deleted on process exit
def make_temp_dir():
    return _tempfile.mkdtemp(prefix="_", dir=_temp_dir)

# This one sticks around
def make_user_temp_dir():
    temp_dir = _tempfile.gettempdir()
    user = _getpass.getuser()
    user_temp_dir = join(temp_dir, user)

    return make_dir(user_temp_dir)

def copy(from_path, to_path):
    notice("Copying {} to {}", from_path, to_path)

    to_dir = parent_dir(to_path)

    if to_dir:
        make_dir(to_dir)

    if is_dir(from_path):
        _copytree(from_path, to_path, symlinks=True)
    else:
        _shutil.copy(from_path, to_path)

def move(from_path, to_path):
    notice("Moving {} to {}", from_path, to_path)

    return _shutil.move(from_path, to_path)

def rename(path, expr, replacement):
    path = normalize_path(path)
    parent_dir, name = split(path)
    to_name = string_replace(name, expr, replacement)
    to_path = join(parent_dir, to_name)

    notice("Renaming {} to {}", path, to_path)

    move(path, to_path)
    
def make_link(source_path, link_file):
    if exists(link_file):
        assert read_link(link_file) == source_path
        return

    _os.symlink(source_path, link_file)

def read_link(file):
    return _os.readlink(file)

def remove(path):
    notice("Removing {}", path)

    if not exists(path):
        return

    if is_dir(path):
        _shutil.rmtree(path, ignore_errors=True)
    else:
        _os.remove(path)

def find(dir, *patterns):
    matched_paths = set()

    if not patterns:
        patterns = ("*",)

    for root, dirs, files in _os.walk(dir):
        for pattern in patterns:
            matched_dirs = _fnmatch.filter(dirs, pattern)
            matched_files = _fnmatch.filter(files, pattern)

            matched_paths.update([join(root, x) for x in matched_dirs])
            matched_paths.update([join(root, x) for x in matched_files])

    return sorted(matched_paths)

# find_via_expr?

def string_replace(string, expr, replacement, count=0):
    return _re.sub(expr, replacement, string, count)

# A regex variant of this?

# Returns the current working directory so you can change it back
def change_dir(dir):
    notice("Changing directory to '{}'", dir)

    cwd = current_dir()
    _os.chdir(dir)
    return cwd

class working_dir(object):
    def __init__(self, dir):
        self.dir = dir
        self.prev_dir = None

    def __enter__(self):
        self.prev_dir = change_dir(self.dir)
        return self.dir

    def __exit__(self, type, value, traceback):
        change_dir(self.prev_dir)

def list_dir(dir, *patterns):
    assert is_dir(dir)

    names = _os.listdir(dir)

    if not patterns:
        return sorted(names)

    matched_names = set()

    for pattern in patterns:
        matched_names.update(_fnmatch.filter(names, pattern))

    return sorted(matched_names)

def first_name(dir, *patterns):
    try:
        return list_dir(dir, *patterns)[0]
    except IndexError:
        return None

def make_dir(dir):
    if not exists(dir):
        _os.makedirs(dir)

    return dir

def _init_call(command, args, kwargs):
    if args:
        command = command.format(*args)

    if "shell" not in kwargs:
        kwargs["shell"] = True

    notice("Calling '{}'", command)

    return command, kwargs

def call(command, *args, **kwargs):
    command, args = _init_call(command, args, kwargs)
    _subprocess.check_call(command, **kwargs)

def call_for_output(command, *args, **kwargs):
    command, args = _init_call(command, args, kwargs)
    return _subprocess.check_output(command, **kwargs)

# Here we mean name without the extension
def make_archive(input_dir, output_dir, archive_stem, format="gztar"):
    temp_dir = make_temp_dir()
    temp_input_dir = join(temp_dir, archive_stem)

    copy(input_dir, temp_input_dir)

    base_output_path = join(output_dir, archive_stem)

    return _shutil.make_archive(base_name=base_output_path,
                                format=format,
                                root_dir=temp_dir,
                                base_dir=archive_stem)

def rename_archive(archive_file, new_archive_stem):
    temp_dir = make_temp_dir()

    with _tarfile.open(archive_file) as f:
        f.extractall(temp_dir)

    archive_name = first_name(temp_dir)
    archive_dir = join(temp_dir, archive_name)
    output_dir = parent_dir(archive_file)

    make_archive(archive_dir, output_dir, new_archive_stem)
    remove(archive_file)

def random_port(min=49152, max=65535):
    return _random.randint(min, max)

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
    names = _os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    if not exists(dst):
        _os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = _os.path.join(src, name)
        dstname = _os.path.join(dst, name)
        try:
            if symlinks and _os.path.islink(srcname):
                linkto = _os.readlink(srcname)
                _os.symlink(linkto, dstname)
            elif _os.path.isdir(srcname):
                _copytree(srcname, dstname, symlinks, ignore)
            else:
                # Will raise a SpecialFileError for unsupported file types
                _shutil.copy2(srcname, dstname)
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except _shutil.Error, err:
            errors.extend(err.args[0])
        except EnvironmentError, why:
            errors.append((srcname, dstname, str(why)))
    try:
        _shutil.copystat(src, dst)
    except OSError, why:
        if _shutil.WindowsError is not None and isinstance \
               (why, _shutil.WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise _shutil.Error, errors
