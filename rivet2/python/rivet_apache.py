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

import xml.etree.ElementTree as _ElementTree

from plano import *
from rivet import *

class ApacheProject(Project):
    def __init__(self, app):
        super(ApacheProject, self).__init__(app, "apache")

        self.activemq = _ActiveMqModule(self, "activemq")
        self.activemq_artemis = _ActiveMqArtemisModule(self, "activemq-artemis")
        self.qpid_cpp = _QpidCppModule(self, "qpid-cpp")
        self.qpid_dispatch = _QpidDispatchModule(self, "qpid-dispatch")
        self.qpid_java = _QpidJavaModule(self, "qpid-java")
        self.qpid_jms = _QpidJmsModule(self, "qpid-jms")
        self.qpid_proton = _QpidProtonModule(self, "qpid-proton")
        self.qpid_proton_j = _QpidProtonJModule(self, "qpid-proton-j")
        self.qpid_python = _QpidPythonModule(self, "qpid-python")

class _SubversionModule(Module):
    def __init__(self, project, name):
        super(_SubversionModule, self).__init__(project, name)

        self.source_url_prefix = "http://svn.apache.org/repos/asf"
        self.source_branch = "trunk"
        self.trunk_url = None
        self.branch_url_spec = None
        self.queried_source_revision = None

    def get_source_url(self, request):
        url = super(_SubversionModule,self).get_source_url(request)

        if url is not None:
            return url

        assert self.source_branch is not None
        assert self.trunk_url is not None
        assert self.branch_url_spec is not None

        if self.source_branch == "trunk":
            return self.trunk_url

        return self.branch_url_spec.replace("@", self.source_branch)

    def get_source_revision(self, request):
        revision = super(_SubversionModule, self).get_source_revision(request)

        if revision is not None:
            return revision

        if self.queried_source_revision is None:
            self.queried_source_revision = self.query_source_revision(request)

        return self.queried_source_revision

    def query_source_revision(self, request):
        url = self.get_source_url(request)
        output = self.call_for_output(request, "svn info {}", url)
        properties = dict()

        for line in output.split(LINE_SEP):
            try:
                name, value = line.split(":", 1)
            except ValueError:
                continue

            properties[name] = value.strip()

        return properties["Last Changed Rev"]

    def do_fetch(self, request):
        info_file = self.get_source_info_file(request)

        if exists(info_file):
            notice("The source is already present")
            return

        source_url = self.get_source_url(request)
        source_branch = self.get_source_branch(request)
        source_revision = self.get_source_revision(request)
        source_dir = self.get_source_dir(request)

        # Subversion wants to make this directory
        remove(source_dir)

        command = "svn export --quiet"

        if source_url.startswith("http"):
            command = "{} --revision {}".format(command, source_revision)

        self.call(request, "{} {} {}", command, source_url, source_dir)

        data = {
            "url": source_url,
            "branch": source_branch,
            "revision": source_revision,
            "date": "XXX",
        }

        write_json(info_file, data)

class _GitModule(Module):
    def __init__(self, project, name):
        super(_GitModule, self).__init__(project, name)

        self.source_url_prefix = "http://git-wip-us.apache.org/repos/asf"
        self.source_branch = "master"
        self.queried_source_revision = None

    def get_source_url(self, request):
        return "{}/{}.git".format(self.source_url_prefix, self.name)

    def get_source_revision(self, request):
        revision = super(_GitModule, self).get_source_revision(request)

        if revision is not None:
            return revision

        if self.queried_source_revision is None:
            self.queried_source_revision = self.query_source_revision(request)

        return self.queried_source_revision

    def query_source_revision(self, request):
        url = self.get_source_url(request)
        branch = self.get_source_branch(request)

        output = self.call_for_output(request, "git ls-remote {} refs/heads/{}", url, branch)
        revision = output.split(None, 1)[0]

        return revision

    def get_shortened_source_revision(self, request):
        source_revision = self.get_source_revision(request)
        return source_revision[0:8]

    def do_fetch(self, request):
        info_file = self.get_source_info_file(request)

        if exists(info_file):
            notice("The source is already present")
            return

        source_url = self.get_source_url(request)
        source_branch = self.get_source_branch(request)
        source_revision = self.get_source_revision(request)
        source_dir = self.get_source_dir(request)

        make_dir(source_dir)

        repo_dir = self.clone_repo(request)

        with working_dir(repo_dir):
            self.call(request, "git archive {} | tar -xf - -C {}", source_revision, source_dir, shell=True)

        data = {
            "url": source_url,
            "branch": source_branch,
            "revision": source_revision,
            "date": "XXX",
        }

        write_json(info_file, data)

    def clone_repo(self, request):
        source_branch = self.get_source_branch(request)
        source_url = self.get_source_url(request)
        repo_dir = make_temp_dir()

        # XXX
        # cmd = "git clone -b {} --single-branch --bare --depth 1 --quiet '{}' {}"
        # self.call(request, cmd, source_branch, source_url, repo_dir)

        self.call(request, "git clone --bare --quiet '{}' {}", source_url, repo_dir)

        return repo_dir

class _PythonModule(Module):
    def do_build(self, request):
        source_dir = self.get_source_dir(request)
        build_dir = self.get_build_dir(request)

        make_dir(build_dir)

        with working_dir(source_dir):
            self.call(request, "python setup.py build --build-base {}", build_dir)

    def do_install(self, request):
        source_dir = self.get_source_dir(request)
        install_dir = self.get_install_dir(request)

        with working_dir(source_dir):
            self.call(request, "python setup.py install --prefix {}", install_dir)

    def do_release(self, request):
        source_dir = self.get_source_dir(request)
        release_dir = self.get_release_dir(request)
        temp_dir = make_temp_dir()
        new_archive_stem = self.get_archive_stem(request)

        make_dir(release_dir)

        with working_dir(source_dir):
            self.call(request, "python setup.py sdist --dist-dir {}", temp_dir)

        release_name = find_only_one(temp_dir, "{}-*".format(self.name))
        archive_file = rename_archive(join(temp_dir, release_name), new_archive_stem)
        archive_file = copy(archive_file, release_dir)

        self.copy_source_info_file(request)
        self.generate_checksums(archive_file)

class _CmakeModule(Module):
    def do_build(self, request):
        source_dir = self.get_source_dir(request)
        build_dir = self.get_build_dir(request)
        install_dir = self.get_install_dir(request)

        make_dir(build_dir)

        with working_dir(build_dir):
            self.call(request, "cmake -DCMAKE_INSTALL_PREFIX={} {}", install_dir, source_dir)
            self.call(request, "make -j {}", request.concurrent_jobs)

    def do_install(self, request):
        build_dir = self.get_build_dir(request)

        with working_dir(build_dir):
            self.call(request, "make install")

    def do_test(self, request):
        build_dir = self.get_build_dir(request)

        with working_dir(build_dir):
            self.call(request, "ctest --output-on-failure")

class _MavenModule(Module):
    def get_project_version(self, request):
        source_dir = self.get_source_dir(request)

        content = read(join(source_dir, "pom.xml"))
        root = _ElementTree.fromstring(content)
        version = root.find("{http://maven.apache.org/POM/4.0.0}version").text

        return version

    def do_build(self, request):
        source_dir = self.get_source_dir(request)
        build_dir = self.get_build_dir(request)

        copy(source_dir, build_dir)

        with working_dir(build_dir):
            self.call(request, "mvn --quiet -DskipTests install")

    def do_test(self, request):
        build_dir = self.get_build_dir(request)

        with working_dir(build_dir):
            self.call(request, "mvn --errors test")

class _ActiveMqModule(_GitModule, _MavenModule):
    def do_install(self, request):
        build_dir = self.get_build_dir(request)
        install_dir = self.get_install_dir(request)
        bin_dir = join(install_dir, "bin")
        opt_dir = join(install_dir, "opt")

        version = self.get_project_version(request)
        archive_name = "apache-activemq-{}".format(version)
        archive_file = join(build_dir, "assembly", "target", "{}-bin.tar.gz".format(archive_name))

        dist_dir = join(opt_dir, archive_name)
        dist_tool = join(dist_dir, "bin", "activemq")
        instance_dir = join(install_dir, "var", "lib", "activemq")
        instance_tool = join(instance_dir, "bin", "activemq")

        remove(dist_dir)
        remove(instance_dir)

        make_dir(opt_dir)

        with working_dir(opt_dir):
            self.call(request, "tar -xf {}", archive_file)

        self.call(request, "{} create {}", dist_tool, instance_dir)

        make_link(instance_tool, join(bin_dir, "activemq"))

class _ActiveMqArtemisModule(_GitModule, _MavenModule):
    def do_install(self, request):
        build_dir = self.get_build_dir(request)
        install_dir = self.get_install_dir(request)
        bin_dir = join(install_dir, "bin")
        opt_dir = join(install_dir, "opt")

        version = self.get_project_version(request)
        archive_name = "apache-artemis-{}".format(version)
        archive_file = join(build_dir, "artemis-distribution", "target", "{}-bin.tar.gz".format(archive_name))

        dist_dir = join(opt_dir, archive_name)
        dist_tool = join(dist_dir, "bin", "artemis")
        instance_dir = join(install_dir, "var", "lib", "artemis")
        instance_tool = join(instance_dir, "bin", "artemis")
        instance_service = join(instance_dir, "bin", "artemis-service")

        remove(dist_dir)
        remove(instance_dir)

        make_dir(opt_dir)

        with working_dir(opt_dir):
            self.call(request, "tar -xf {}", archive_file)

        self.call(request, "{} create {} --user admin --password admin --role admin --allow-anonymous", dist_tool, instance_dir)

        make_link(instance_tool, join(bin_dir, "artemis"))
        make_link(instance_service, join(bin_dir, "artemis-service"))

class _QpidProtonModule(_GitModule, _CmakeModule):
    pass

class _QpidProtonJModule(_GitModule, _MavenModule):
    pass

class _QpidJmsModule(_GitModule, _MavenModule):
    pass

class _QpidDispatchModule(_GitModule, _CmakeModule):
    def do_build(self, request):
        source_dir = self.get_source_dir(request)
        build_dir = self.get_build_dir(request)
        install_dir = self.get_install_dir(request)
        proton_include_dir = self.app.get_include_dir(request)
        lib_dir = self.app.get_lib_dir(request)
        proton_lib = join(lib_dir, "libqpid-proton.so")

        self.project.qpid_proton.install(request)

        make_dir(build_dir)

        with working_dir(build_dir):
            cmd = "cmake -DCMAKE_INSTALL_PREFIX={} -Dproton_include={} " \
                  "-Dproton_lib={} {}"

            self.call(request, cmd, install_dir, proton_include_dir,
                      proton_lib, source_dir)
            self.call(request, "make -j {}", request.concurrent_jobs)

class _QpidPythonModule(_GitModule, _PythonModule):
    def do_test(self, request):
        self.call(request, "qpid-python-test --list")

class _QpidCppModule(_GitModule, _CmakeModule):
    def do_build(self, request):
        source_dir = self.get_source_dir(request)
        build_dir = self.get_build_dir(request)
        install_dir = self.get_install_dir(request)
        plat_python_dir = self.app.get_python_plat_lib_dir(request)
        plat_lib_dir = parent_dir(parent_dir(plat_python_dir))
        proton_cmake_dir = join(plat_lib_dir, "cmake", "Proton")

        self.project.qpid_proton.install(request)

        make_dir(build_dir)

        with working_dir(build_dir):
            cmd = "cmake -DCMAKE_INSTALL_PREFIX={} -DProton_DIR={} {}"

            self.call(request, cmd, install_dir, proton_cmake_dir, source_dir)
            self.call(request, "make -j {}", request.concurrent_jobs)

    def do_test(self, request):
        self.project.qpid_python.install(request)

        super(_QpidCppModule, self).do_test(request)

    def do_uninstall(self, request):
        build_dir = self.get_build_dir(request)

        with working_dir(build_dir):
            self.call(request, "make uninstall")

class _QpidJavaModule(_SubversionModule, _MavenModule):
    def __init__(self, project, name):
        super(_QpidJavaModule, self).__init__(project, name)

        self.trunk_url = "{}/qpid/java/trunk".format(self.source_url_prefix)
        self.branch_url_spec = "{}/qpid/java/branches/@".format \
                               (self.source_url_prefix)
