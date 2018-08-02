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

from datetime import datetime as _datetime
from functools import wraps as _wraps

import collections as _collections
import distutils.sysconfig as _sysconfig
import inspect as _inspect
import multiprocessing as _multiprocessing
import os as _os
import plano as _plano
import subprocess as _subprocess
import sys as _sys
import traceback as _traceback
import types as _types

class _Object(object):
    def __init__(self, name=None):
        self.name = name

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.name)

class Rivet(_Object):
    def __init__(self, home):
        super(Rivet, self).__init__()

        self.home = home

        self.commands = list()
        self.commands_by_name = dict()

        self.projects = list()
        self.projects_by_name = dict()

        _Command(self, "info")
        _Command(self, "fetch")
        _Command(self, "build")
        _Command(self, "install")
        _Command(self, "uninstall")
        _ReleaseCommand(self, "release")
        _Command(self, "test-build")
        _Command(self, "test-install")
        _Command(self, "test-release")
        _Command(self, "test")
        _CleanCommand(self, "clean")
        _EnvCommand(self, "env")

    def load(self):
        for project in self.projects:
            project.load()

    def init(self):
        for project in self.projects:
            project.init()

    def get_source_dir(self, request):
        return _plano.join(request.output_dir, "source")

    def get_release_dir(self, request):
        return _plano.join(request.output_dir, "release")

    def get_build_dir(self, request):
        return _plano.join(request.output_dir, "build")

    def get_install_dir(self, request):
        return request.install_dir

    def get_install_env(self, request):
        install_dir = self.get_install_dir(request)
        bin_dir = self.get_bin_dir(request)
        sbin_dir = self.get_sbin_dir(request)
        lib_dir = self.get_lib_dir(request)
        include_dir = self.get_include_dir(request)
        python_dir = self.get_python_lib_dir(request)
        plat_python_dir = self.get_python_plat_lib_dir(request)

        env = dict()

        def add_path_var(name, *args):
            elems = [x for x in args if x not in ("", None)]

            if name in _plano.ENV:
                elems.append(_plano.ENV[name])

            env[name] = ":".join(elems)

        add_path_var("C_INCLUDE_PATH", include_dir)
        add_path_var("CPLUS_INCLUDE_PATH", include_dir)
        add_path_var("LD_LIBRARY_PATH", lib_dir)
        add_path_var("LIBRARY_PATH", lib_dir)
        add_path_var("PATH", bin_dir, sbin_dir)
        add_path_var("PYTHONPATH", plat_python_dir, python_dir)

        return env

    def get_bin_dir(self, request):
        return _plano.join(request.install_dir, "bin")

    def get_sbin_dir(self, request):
        return _plano.join(request.install_dir, "sbin")

    def get_include_dir(self, request):
        return _plano.join(request.install_dir, "include")

    def get_lib_dir(self, request):
        if _sys.maxsize > 2**32:
            return _plano.join(request.install_dir, "lib64")

        return _plano.join(request.install_dir, "lib64")

    def get_python_lib_dir(self, request):
        return _sysconfig.get_python_lib(False, False, request.install_dir)

    def get_python_plat_lib_dir(self, request):
        return _sysconfig.get_python_lib(True, False, request.install_dir)

class Request(_Object):
    def __init__(self, output_dir):
        super(Request, self).__init__()

        self.output_dir = _plano.absolute_path(output_dir)

        self.all_modules = False
        self.modules = list()
        self.source_revisions_by_module = dict()

        self.concurrent_jobs = _multiprocessing.cpu_count()
        self.install_dir = _plano.join(self.output_dir, "install")
        self.release_tag = None

        self.visited_tasks = set()
        self.failed_tasks = dict()

        self.date = _datetime.now().strftime("%Y%m%d")

class Project(_Object):
    def __init__(self, app, name):
        super(Project, self).__init__(name)

        self.app = app

        self.modules = list()
        self.modules_by_name = dict()

        assert self.name not in self.app.projects_by_name

        self.app.projects.append(self)
        self.app.projects_by_name[self.name] = self

    def load(self):
        for module in self.modules:
            module.load()

    def init(self):
        for module in self.modules:
            module.init()

class Module(_Object):
    def __init__(self, project, name):
        super(Module, self).__init__(name)

        self.project = project
        self.app = project.app

        self.source_url = None
        self.source_branch = None
        self.source_revision = None

        self.release_tag = None

        assert name not in self.project.modules_by_name

        self.project.modules.append(self)
        self.project.modules_by_name[self.name] = self

        self.info = _Task(self, "info")
        self.clean = _Task(self, "clean")
        self.fetch = _FetchTask(self, "fetch")
        self.build = _BuildTask(self, "build")
        self.install = _InstallTask(self, "install")
        self.release = _ReleaseTask(self, "release")
        self.test = _TestTask(self, "test")

    def load(self):
        if self.release_tag is None:
            date = _datetime.now().strftime("%Y%m%d")
            self.release_tag = "{}-{}".format(self.source_branch, date)

    def init(self):
        pass

    def get_source_url(self, request):
        return self.source_url

    def get_source_branch(self, request):
        return self.source_branch

    def get_source_revision(self, request):
        revision = request.source_revisions_by_module.get(self)

        if revision is not None:
            return revision

        info_file = self.get_source_info_file(request)

        if _plano.exists(info_file):
            info = _plano.read_json(info_file)
            return info["revision"]

        return self.source_revision

    def get_source_info_file(self, request):
        source_dir = self.get_source_dir(request)
        return "{}.json".format(source_dir)

    def get_shortened_source_revision(self, request):
        return self.get_source_revision(request)

    def get_source_dir(self, request):
        return _plano.join(self.app.get_source_dir(request), self.name)

    def get_build_dir(self, request):
        return _plano.join(self.app.get_build_dir(request), self.name)

    def get_install_dir(self, request):
        return self.app.get_install_dir(request)

    def get_release_dir(self, request):
        return _plano.join(self.app.get_release_dir(request), self.name)

    def get_release_tag(self, request):
        if request.release_tag is not None:
            return request.release_tag

        source_branch = self.get_source_branch(request)
        source_revision = self.get_shortened_source_revision(request)

        return "{}-{}-{}".format(source_branch, request.date, source_revision)

    def get_archive_stem(self, request):
        release_tag = self.get_release_tag(request)
        return "{}-{}".format(self.name, release_tag)

    def call(self, request, command, *args, **kwargs):
        kwargs["env"] = self.app.get_install_env(request)
        _plano.call(command, *args, **kwargs)

    def call_for_output(self, request, command, *args, **kwargs):
        kwargs["env"] = self.app.get_install_env(request)
        return _plano.call_for_output(command, *args, **kwargs)

    def do_info(self, request):
        source_url = self.get_source_url(request)
        source_branch = self.get_source_branch(request)
        source_revision = self.get_source_revision(request)
        source_dir = self.get_source_dir(request)
        build_dir = self.get_build_dir(request)
        release_tag = self.get_release_tag(request)

        print("Module '{}':".format(self.name))
        print("  Source URL:        {}".format(source_url))
        print("  Source branch:     {}".format(source_branch))
        print("  Source revision:   {}".format(source_revision))
        print("  Source dir:        {}".format(source_dir))
        print("  Build dir:         {}".format(build_dir))
        print("  Release tag:       {}".format(release_tag))

    def do_clean(self, request):
        source_dir = self.get_source_dir(request)
        info_file = self.get_source_info_file(request)
        build_dir = self.get_build_dir(request)
        release_dir = self.get_release_dir(request)

        _plano.remove(source_dir)
        _plano.remove(build_dir)
        _plano.remove(release_dir)
        _plano.remove(info_file)

    def do_release(self, request):
        source_dir = self.get_source_dir(request)
        release_dir = self.get_release_dir(request)
        archive_stem = self.get_archive_stem(request)

        archive_file = _plano.make_archive(source_dir, release_dir, archive_stem)

        self.copy_source_info_file(request)
        self.generate_checksums(archive_file)

    def copy_source_info_file(self, request):
        info_file = self.get_source_info_file(request)
        release_dir = self.get_release_dir(request)
        archive_stem = self.get_archive_stem(request)
        release_info_file = "{}.json".format(_plano.join(release_dir, archive_stem))

        _plano.copy(info_file, release_info_file)

    def generate_checksums(self, archive_file):
        release_dir, archive_name = _plano.split(archive_file)

        with _plano.working_dir(release_dir):
            with open("{}.md5".format(archive_name), "w") as f:
                _plano.call("md5sum {}", archive_name, stdout=f)

            with open("{}.sha".format(archive_name), "w") as f:
                _plano.call("sha512sum {}", archive_name, stdout=f)

    def do_fetch(self, request):
        raise NotImplementedError()

    def do_build(self, request):
        raise NotImplementedError()

    def do_install(self, request):
        pass

    def do_test(self, request):
        raise NotImplementedError()

class _Command(_Object):
    def __init__(self, app, name):
        super(_Command, self).__init__(name)

        self.app = app
        self.method_name = self.name.replace("-", "_")

        assert self.name not in self.app.commands_by_name

        self.app.commands.append(self)
        self.app.commands_by_name[self.name] = self

    def __call__(self, request):
        for module in request.modules:
            task = getattr(module, self.method_name)
            task(request)

class _ReleaseCommand(_Command):
    def __call__(self, request):
        super(_ReleaseCommand, self).__call__(request)

        release_dir = self.app.get_release_dir(request)

        print("Current release files:")

        for file_ in _plano.find(release_dir):
            print("  {}".format(file_))

class _CleanCommand(_Command):
    def __call__(self, request):
        super(_CleanCommand, self).__call__(request)

        install_dir = self.app.get_install_dir(request)

        if install_dir.startswith(request.output_dir) and request.all_modules is True:
            _plano.remove(install_dir)

class _EnvCommand(_Command):
    def __call__(self, request):
        env = self.app.get_install_env(request)

        # XXX Factor in project-specific install env settings

        for name in sorted(env):
            value = env[name]
            print("export {}={}".format(name, value))

class _Task(object):
    def __init__(self, module, name):
        self.module = module
        self.name = name

        method_name = "do_{}".format(self.name.replace("-", "_"))
        self.method = getattr(self.module, method_name)

    def __repr__(self):
        return "{}({})".format(self.name, self.module.name)

    def __call__(self, request):
        if self in request.visited_tasks:
            return

        request.visited_tasks.add(self)

        _plano.notice("Starting {}", self)

        try:
            self.do_call(request)
        except KeyboardInterrupt:
            raise
        except _subprocess.CalledProcessError as e:
            request.failed_tasks[self] = e
            _plano.notice("Call failed: {}", str(e))
        except Exception as e:
            request.failed_tasks[self] = e
            _traceback.print_exc()
            _plano.error(e)

        _plano.notice("Finished {}", self)

    def do_call(self, request):
        self.method(request)

class _FetchTask(_Task):
    def do_call(self, request):
        super(_FetchTask, self).do_call(request)

class _BuildTask(_Task):
    def do_call(self, request):
        self.module.fetch(request)

        super(_BuildTask, self).do_call(request)

class _InstallTask(_Task):
    def do_call(self, request):
        self.module.build(request)

        super(_InstallTask, self).do_call(request)

class _ReleaseTask(_Task):
    def do_call(self, request):
        self.module.fetch(request)

        super(_ReleaseTask, self).do_call(request)

class _TestTask(_Task):
    def do_call(self, request):
        self.module.install(request)
        self.module.release(request)

        super(_TestTask, self).do_call(request)
