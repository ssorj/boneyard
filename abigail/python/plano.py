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
import binascii as _binascii
import codecs as _codecs
import collections as _collections
import ctypes as _ctypes
import fnmatch as _fnmatch
import getpass as _getpass
import json as _json
import os as _os
import random as _random
import re as _re
import shlex as _shlex
import shutil as _shutil
import signal as _signal
import socket as _socket
import subprocess as _subprocess
import sys as _sys
import tarfile as _tarfile
import tempfile as _tempfile
import time as _time
import traceback as _traceback
import types as _types
import uuid as _uuid

from subprocess import CalledProcessError
from subprocess import PIPE

# See documentation at http://www.ssorj.net/projects/plano.html

class PlanoException(Exception):
    pass

LINE_SEP = _os.linesep
PATH_SEP = _os.sep
PATH_VAR_SEP = _os.pathsep
ENV = _os.environ
ARGS = _sys.argv

STD_IN = _sys.stdin
STD_OUT = _sys.stdout
STD_ERR = _sys.stderr
NULL_DEV = _os.devnull

_message_levels = (
    "debug",
    "notice",
    "warn",
    "error",
)

_debug = _message_levels.index("debug")
_notice = _message_levels.index("notice")
_warn = _message_levels.index("warn")
_error = _message_levels.index("error")

_message_output = STD_ERR
_message_threshold = _notice

def set_message_output(writeable):
    global _message_output
    _message_output = writeable

def set_message_threshold(level):
    assert level in _message_levels

    global _message_threshold
    _message_threshold = _message_levels.index(level)

def fail(message, *args):
    error(message, *args)

    if isinstance(message, BaseException):
        raise message

    raise PlanoException(message.format(*args))

def error(message, *args):
    _print_message("Error", message, args)

def warn(message, *args):
    if _message_threshold <= _warn:
        _print_message("Warning", message, args)

def notice(message, *args):
    if _message_threshold <= _notice:
        _print_message(None, message, args)

def debug(message, *args):
    if _message_threshold <= _debug:
        _print_message("Debug", message, args)

def exit(arg=None, *args):
    if arg in (0, None):
        _sys.exit()

    if _is_string(arg):
        error(arg, args)
        _sys.exit(1)
    elif isinstance(arg, _types.IntType):
        if arg > 0:
            error("Exiting with code {0}", arg)
        else:
            notice("Exiting with code {0}", arg)

        _sys.exit(arg)
    else:
        raise Exception()

def _print_message(category, message, args):
    if _message_output is None:
        return

    message = _format_message(category, message, args)

    print(message, file=_message_output)

    _message_output.flush()

def _format_message(category, message, args):
    if not _is_string(message):
        message = str(message)

    if args:
        message = message.format(*args)

    if len(message) > 0 and message[0].islower():
        message = message[0].upper() + message[1:]

    if category:
        message = "{0}: {1}".format(category, message)

    program = program_name()
    message = "{0}: {1}".format(program, message)

    return message

def eprint(*args, **kwargs):
    print(*args, file=_sys.stderr, **kwargs)

def flush():
    _sys.stdout.flush()
    _sys.stderr.flush()

absolute_path = _os.path.abspath
normalize_path = _os.path.normpath
real_path = _os.path.realpath
exists = _os.path.exists
is_absolute = _os.path.isabs
is_dir = _os.path.isdir
is_file = _os.path.isfile
is_link = _os.path.islink
file_size = _os.path.getsize

join = _os.path.join
split = _os.path.split
split_extension = _os.path.splitext

current_dir = _os.getcwd
sleep = _time.sleep

def home_dir(user=None):
    return _os.path.expanduser("~{0}".format(user or ""))

def parent_dir(path):
    path = normalize_path(path)
    parent, child = split(path)

    return parent

def file_name(file):
    file = normalize_path(file)
    dir, name = split(file)

    return name

def name_stem(file):
    name = file_name(file)

    if name.endswith(".tar.gz"):
        name = name[:-3]

    stem, ext = split_extension(name)

    return stem

def name_extension(file):
    name = file_name(file)
    stem, ext = split_extension(name)

    return ext

def program_name(command=None):
    if command is None:
        args = ARGS
    else:
        args = command.split()

    for arg in args:
        if "=" not in arg:
            return file_name(arg)

def which(program_name):
    for dir in ENV["PATH"].split(PATH_VAR_SEP):
        program = join(dir, program_name)

        if _os.access(program, _os.X_OK):
            return program

def read(file):
    with _codecs.open(file, encoding="utf-8", mode="r") as f:
        return f.read()

def write(file, string):
    with _codecs.open(file, encoding="utf-8", mode="w") as f:
        f.write(string)

    return file

def append(file, string):
    with _codecs.open(file, encoding="utf-8", mode="a") as f:
        f.write(string)

    return file

def prepend(file, string):
    orig = read(file)
    prepended = string + orig

    return write(file, prepended)

# XXX Should this work on directories?
def touch(file):
    return append(file, "")

def tail(file, n):
    return "".join(tail_lines(file, n))

def read_lines(file):
    with _codecs.open(file, encoding="utf-8", mode="r") as f:
        return f.readlines()

def write_lines(file, lines):
    with _codecs.open(file, encoding="utf-8", mode="r") as f:
        f.writelines(lines)

    return file

def append_lines(file, lines):
    with _codecs.open(file, encoding="utf-8", mode="a") as f:
        f.writelines(string)

    return file

def prepend_lines(file, lines):
    orig_lines = read_lines(file)

    with _codecs.open(file, encoding="utf-8", mode="w") as f:
        f.writelines(lines)
        f.writelines(orig_lines)

    return file

# Derived from http://stackoverflow.com/questions/136168/get-last-n-lines-of-a-file-with-python-similar-to-tail
def tail_lines(file, n):
    assert n >= 0

    with _codecs.open(file, encoding="utf-8", mode="r") as f:
        pos = n + 1
        lines = list()

        while len(lines) <= n:
                try:
                    f.seek(-pos, 2)
                except IOError:
                    f.seek(0)
                    break
                finally:
                    lines = f.readlines()

                pos *= 2

        return lines[-n:]

def read_json(file):
    with _codecs.open(file, encoding="utf-8", mode="r") as f:
        return _json.load(f)

def write_json(file, obj):
    with _codecs.open(file, encoding="utf-8", mode="w") as f:
        return _json.dump(obj, f, indent=4, separators=(",", ": "), sort_keys=True)

def make_temp_file(suffix=""):
    try:
        dir = ENV["XDG_RUNTIME_DIR"]
    except KeyError:
        dir = None

    return _tempfile.mkstemp(prefix="plano-", suffix=suffix, dir=dir)[1]

def make_temp_dir(suffix=""):
    try:
        dir = ENV["XDG_RUNTIME_DIR"]
    except KeyError:
        dir = None

    return _tempfile.mkdtemp(prefix="plano-", suffix=suffix, dir=dir)

class temp_file(object):
    def __init__(self, suffix=""):
        self.file = make_temp_file(suffix=suffix)

    def __enter__(self):
        return self.file

    def __exit__(self, exc_type, exc_value, traceback):
        if exists(self.file):
            _os.remove(self.file)

class temp_dir(object):
    def __init__(self, suffix=""):
        self.dir = make_temp_dir(suffix=suffix)

    def __enter__(self):
        return self.dir

    def __exit__(self, exc_type, exc_value, traceback):
        if exists(self.dir):
            _shutil.rmtree(self.dir, ignore_errors=True)

def unique_id(length=16):
    assert length >= 1
    assert length <= 16

    uuid_bytes = _uuid.uuid4().bytes
    uuid_bytes = uuid_bytes[:length]

    return _binascii.hexlify(uuid_bytes).decode("utf-8")

def copy(from_path, to_path):
    notice("Copying '{0}' to '{1}'", from_path, to_path)

    if is_dir(to_path):
        to_path = join(to_path, file_name(from_path))
    else:
        make_dir(parent_dir(to_path))

    if is_dir(from_path):
        _copytree(from_path, to_path, symlinks=True)
    else:
        _shutil.copy(from_path, to_path)

    return to_path

def move(from_path, to_path):
    notice("Moving '{0}' to '{1}'", from_path, to_path)

    if is_dir(to_path):
        to_path = join(to_path, file_name(from_path))
    else:
        make_dir(parent_dir(to_path))

    _shutil.move(from_path, to_path)

    return to_path

def rename(path, expr, replacement):
    path = normalize_path(path)
    parent_dir, name = split(path)
    to_name = string_replace(name, expr, replacement)
    to_path = join(parent_dir, to_name)

    notice("Renaming '{0}' to '{1}'", path, to_path)

    move(path, to_path)

    return to_path

def remove(path):
    notice("Removing '{0}'", path)

    if not exists(path):
        return

    if is_dir(path):
        _shutil.rmtree(path, ignore_errors=True)
    else:
        _os.remove(path)

    return path

def make_link(source_path, link_file):
    notice("Making link '{0}' to '{1}'", link_file, source_path)

    if exists(link_file):
        assert read_link(link_file) == source_path
        return

    link_dir = parent_dir(link_file)

    if link_dir:
        make_dir(link_dir)

    _os.symlink(source_path, link_file)

    return link_file

def read_link(file):
    return _os.readlink(file)

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

def find_any_one(dir, *patterns):
    paths = find(dir, *patterns)

    if len(paths) == 0:
        return

    return paths[0]

def find_only_one(dir, *patterns):
    paths = find(dir, *patterns)

    if len(paths) == 0:
        return

    assert len(paths) == 1

    return paths[0]

# find_via_expr?

def string_replace(string, expr, replacement, count=0):
    return _re.sub(expr, replacement, string, count)

def make_dir(dir):
    if not exists(dir):
        _os.makedirs(dir)

    return dir

# Returns the current working directory so you can change it back
def change_dir(dir):
    notice("Changing directory to '{0}'", dir)

    cwd = current_dir()
    _os.chdir(dir)
    return cwd

def list_dir(dir, *patterns):
    assert is_dir(dir)

    names = _os.listdir(dir)

    if not patterns:
        return sorted(names)

    matched_names = set()

    for pattern in patterns:
        matched_names.update(_fnmatch.filter(names, pattern))

    return sorted(matched_names)

class working_dir(object):
    def __init__(self, dir):
        self.dir = dir
        self.prev_dir = None

    def __enter__(self):
        self.prev_dir = change_dir(self.dir)
        return self.dir

    def __exit__(self, exc_type, exc_value, traceback):
        change_dir(self.prev_dir)

class temp_working_dir(working_dir):
    def __init__(self):
        super(temp_working_dir, self).__init__(make_temp_dir())

    def __exit__(self, exc_type, exc_value, traceback):
        super(temp_working_dir, self).__exit__(exc_type, exc_value, traceback)

        if exists(self.dir):
            _shutil.rmtree(self.dir, ignore_errors=True)

def call(command, *args, **kwargs):
    proc = start_process(command, *args, **kwargs)
    check_process(proc)

def call_for_exit_code(command, *args, **kwargs):
    proc = start_process(command, *args, **kwargs)
    return wait_for_process(proc)

def call_for_output(command, *args, **kwargs):
    kwargs["stdout"] = _subprocess.PIPE

    proc = start_process(command, *args, **kwargs)
    output = proc.communicate()[0]
    exit_code = proc.poll()

    # XXX I don't know if None is possible here
    assert exit_code is not None

    if exit_code not in (None, 0):
        error = CalledProcessError(exit_code, proc.command_string)
        error.output = output

        raise error

    return output

def call_and_print_on_error(command, *args, **kwargs):
    with temp_file() as output_file:
        try:
            with open(output_file, "w") as out:
                kwargs["output"] = out
                call(command, *args, **kwargs)
        except CalledProcessError:
            eprint(read(output_file), end="")
            raise

_child_processes = list()

class _Process(_subprocess.Popen):
    def __init__(self, command, options, name, command_string):
        super(_Process, self).__init__(command, **options)

        self.name = name
        self.command_string = command_string

        _child_processes.append(self)

    @property
    def exit_code(self):
        return self.returncode

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        stop_process(self.proc)

    def __repr__(self):
        return "process {0} ({1})".format(self.pid, self.name)

def default_sigterm_handler(signum, frame):
    for proc in _child_processes:
        if proc.poll() is None:
            proc.terminate()

    #_remove_temp_dir()

    exit(-(_signal.SIGTERM))

_signal.signal(_signal.SIGTERM, default_sigterm_handler)

def _command_string(command, args):
    elems = ["\"{0}\"".format(x) if " " in x else x for x in command]
    string = " ".join(elems)
    string = string.format(*args)

    return string

_libc = None

if _sys.platform == "linux2":
    try:
        _libc = _ctypes.CDLL(_ctypes.util.find_library("c"))
    except:
        _traceback.print_exc()

def start_process(command, *args, **kwargs):
    if _is_string(command):
        command = command.format(*args)
        command_args = _shlex.split(command)
        command_string = command
    elif isinstance(command, _collections.Iterable):
        assert len(args) == 0, args
        command_args = command
        command_string = _command_string(command, [])
    else:
        raise Exception()

    notice("Calling '{0}'", command_string)

    name = kwargs.get("name", command_args[0])

    kwargs["stdout"] = kwargs.get("stdout", _sys.stdout)
    kwargs["stderr"] = kwargs.get("stderr", _sys.stderr)

    if "output" in kwargs:
        out = kwargs.pop("output")

        kwargs["stdout"] = out
        kwargs["stderr"] = out

    if "preexec_fn" not in kwargs:
        if _libc is not None:
            kwargs["preexec_fn"] = _libc.prctl(1, _signal.SIGKILL)

    if "shell" in kwargs and kwargs["shell"] is True:
        proc = _Process(command_string, kwargs, name, command_string)
    else:
        proc = _Process(command_args, kwargs, name, command_string)

    debug("{0} started", proc)

    return proc

def terminate_process(proc):
    notice("Terminating {0}", proc)

    if proc.poll() is None:
        proc.terminate()
    else:
        debug("{0} already exited", proc)

def stop_process(proc):
    notice("Stopping {0}", proc)

    if proc.poll() is not None:
        if proc.returncode == 0:
            debug("{0} already exited normally", proc)
        elif proc.returncode == -(_signal.SIGTERM):
            debug("{0} was already terminated", proc)
        else:
            debug("{0} already exited with code {1}", proc, proc.returncode)

        return

    proc.terminate()

    return wait_for_process(proc)

def wait_for_process(proc):
    debug("Waiting for {0} to exit", proc)

    proc.wait()

    if proc.returncode == 0:
        debug("{0} exited normally", proc)
    elif proc.returncode == -(_signal.SIGTERM):
        debug("{0} exited after termination", proc)
    else:
        debug("{0} exited with code {1}", proc, proc.returncode)

    return proc.returncode

def check_process(proc):
    wait_for_process(proc)

    if proc.returncode != 0:
        raise CalledProcessError(proc.returncode, proc.command_string)

def exec_process(command, *args):
    if _is_string(command):
        command = command.format(*args)
        command_args = _shlex.split(command)
        command_string = command
    elif isinstance(command, _collections.Iterable):
        assert len(args) == 0, args
        command_args = command
        command_string = _command_string(command, [])
    else:
        raise Exception()

    notice("Calling '{0}'", command_string)

    _os.execvp(command_args[0], command_args[1:])

def make_archive(input_dir, output_dir, archive_stem):
    assert is_dir(input_dir), input_dir
    assert is_dir(output_dir), output_dir
    assert _is_string(archive_stem), archive_stem

    with temp_dir() as dir:
        temp_input_dir = join(dir, archive_stem)

        copy(input_dir, temp_input_dir)
        make_dir(output_dir)

        output_file = "{0}.tar.gz".format(join(output_dir, archive_stem))
        output_file = absolute_path(output_file)

        with working_dir(dir):
            call("tar -czf {0} {1}", output_file, archive_stem)

    return output_file

def extract_archive(archive_file, output_dir):
    assert is_file(archive_file), archive_file
    assert is_dir(output_dir), output_dir

    make_dir(output_dir)

    archive_file = absolute_path(archive_file)

    with working_dir(output_dir):
        call("tar -xf {0}", archive_file)

    return output_dir

def rename_archive(archive_file, new_archive_stem):
    assert is_file(archive_file), archive_file
    assert _is_string(new_archive_stem), new_archive_stem

    if name_stem(archive_file) == new_archive_stem:
        return archive_file

    with temp_dir() as dir:
        extract_archive(archive_file, dir)

        input_name = list_dir(dir)[0]
        input_dir = join(dir, input_name)
        output_file = make_archive(input_dir, dir, new_archive_stem)
        output_name = file_name(output_file)
        archive_dir = parent_dir(archive_file)
        new_archive_file = join(archive_dir, output_name)

        move(output_file, new_archive_file)
        remove(archive_file)

    return new_archive_file

def random_port(min=49152, max=65535):
    return _random.randint(min, max)

def wait_for_port(port, host="", timeout=30):
    if _is_string(port):
        port = int(port)

    sock = _socket.socket(_socket.AF_INET, _socket.SOCK_STREAM)
    sock.setsockopt(_socket.SOL_SOCKET, _socket.SO_REUSEADDR, 1)

    start = _time.time()

    try:
        while True:
            if sock.connect_ex((host, port)) == 0:
                return

            sleep(0.1)

            if _time.time() - start > timeout:
                fail("Timed out waiting for port {0} to open", port)
    finally:
        sock.close()

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
        except _shutil.Error as err:
            errors.extend(err.args[0])
        except EnvironmentError as why:
            errors.append((srcname, dstname, str(why)))
    try:
        _shutil.copystat(src, dst)
    except OSError as why:
        if _shutil.WindowsError is not None and isinstance \
               (why, _shutil.WindowsError):
            # Copying file access times may fail on Windows
            pass
        else:
            errors.append((src, dst, str(why)))
    if errors:
        raise _shutil.Error(errors)

def _is_string(obj):
    try:
        return isinstance(obj, basestring)
    except NameError:
        return isinstance(obj, str)
