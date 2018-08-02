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

import collections as _collections
import getpass as _getpass
import json as _json
import os as _os
import pprint as _pprint
import tempfile as _tempfile
import urllib as _urllib

class Model(object):
    def __init__(self, base_url, project_keys):
        self.base_url = base_url
        self.project_keys = project_keys

        self.projects = list()
        self.projects_by_key = dict()

        self.statuses = list()
        self.statuses_by_id = dict()

        self.resolutions = list()
        self.resolutions_by_id = dict()

    def get_json_data(self, url_path, resource_name):
        name = "{}.json".format(resource_name)
        path = self.get_local_path(name)

        if not _os.path.exists(path):
            url = "{}/rest/api/2/{}".format(self.base_url, url_path)
            _urllib.urlretrieve(url, path)

        with open(path, "r") as file:
            return _json.load(file)

    def get_local_path(self, name):
        dir = _os.path.join(_tempfile.gettempdir(), _getpass.getuser(), "lintel")
        path = _os.path.join(dir, name)

        if not _os.path.exists(dir):
            _os.makedirs(dir)

        return path

    def load(self):
        json_statuses = self.get_json_data("status", "statuses")
        json_resolutions = self.get_json_data("resolution", "resolutions")
        # priorities

        for json_status in json_statuses:
            status = _Status(self, json_status["id"])
            status.name = json_status["name"]
            status.description = json_status.get("description")

        for json_resolution in json_resolutions:
            resolution = _Resolution(self, json_resolution["id"])
            resolution.name = json_resolution["name"]
            resolution.description = json_resolution.get("description")

        for key in self.project_keys:
            url_path = "project/{}".format(key)
            resource_name = "project-{}".format(key)
            json_project = self.get_json_data(url_path, resource_name)

            project = _Project(self, json_project["id"])
            project.json_data = json_project
            project.load()

    def pretty_print(self):
        for project in self.projects:
            project.pretty_print()

class _ModelObject(object):
    def __init__(self, model, id):
        self.model = model
        self.id = id
        self.name = None
        self.description = None

    def copy(self):
        other = self.__class__(self.model, self.id)
        other.name = self.name
        other.description = self.description

        return other

class _Status(_ModelObject):
    def __init__(self, model, id):
        super(_Status, self).__init__(model, id)

        self.model.statuses.append(self)
        self.model.statuses_by_id[self.id] = self

class _Resolution(_ModelObject):
    def __init__(self, model, id):
        super(_Resolution, self).__init__(model, id)

        self.model.resolutions.append(self)
        self.model.resolutions_by_id[self.id] = self

class _Project(_ModelObject):
    def __init__(self, model, id):
        super(_Project, self).__init__(model, id)

        self.key = None

        self.json_data = None

        self.components = list()
        self.components_by_id = dict()

        self.versions = list()
        self.versions_by_id = dict()

        self.assignees = list()
        self.assignees_by_id = dict()

        self.queries = list()
        self.operations = list()

        self.model.projects.append(self)

    def load(self):
        self.name = self.json_data["name"]
        self.key = self.json_data["key"]

        self.model.projects_by_key[self.key] = self

        query = _Query(self.model, "all")
        query.name = "All"
        query.set_project(self)

        query = _Query(self.model, "unresolved")
        query.name = "Unresolved"
        query.add("resolution", None)
        query.set_project(self)

        query = _Query(self.model, "open")
        query.name = "Open"
        query.add("status", "Open")
        query.set_project(self)

        query = _Query(self.model, "coding-in-progress")
        query.name = "In progress"
        query.add("status", "Coding In Progress")
        query.set_project(self)

        query = _Query(self.model, "resolved")
        query.name = "Resolved"
        query.add("status", "Resolved")
        query.set_project(self)

        query = _Query(self.model, "closed")
        query.name = "Closed"
        query.add("status", "Closed")
        query.set_project(self)

        query = _Query(self.model, "reopened")
        query.name = "Reopened"
        query.add("status", "Reopened")
        query.set_project(self)

        # query = _Query(self.model, "unresolved-bugs")
        # query.name = "Unresolved bugs"
        # query.add("resolution", None)
        # query.add("issuetype", "Bug")
        # query.set_project(self)

        # query = _Query(self.model, "unresolved-enhancements")
        # query.name = "Unresolved enhancements"
        # query.add("resolution", None)
        # query.add("issuetype", ("New Feature", "Improvement"))
        # query.set_project(self)

        # query = _Query(self.model, "unresolved-tasks")
        # query.name = "Unresolved tasks"
        # query.add("resolution", None)
        # query.add("issuetype", "Task")
        # query.set_project(self)

        # query = _Query(self.model, "fixed-bugs")
        # query.name = "Fixed bugs"
        # query.add("resolution", "Fixed")
        # query.add("issuetype", "Bug")
        # query.set_project(self)

        # query = _Query(self.model, "resolved-bugs")
        # query.name = "Resolved bugs"
        # query.add("resolution", None, "is not")
        # query.add("issuetype", "Bug")
        # query.set_project(self)

        # query = _Query(self.model, "completed-enhancements")
        # query.name = "Completed enhancements"
        # query.add("resolution", "Fixed")
        # query.add("issuetype", ("New Feature", "Improvement"))
        # query.set_project(self)

        # query = _Query(self.model, "resolved-enhancements")
        # query.name = "Resolved enhancements"
        # query.add("resolution", None, "is not")
        # query.add("issuetype", ("New Feature", "Improvement"))
        # query.set_project(self)

        # query = _Query(self.model, "completed-tasks")
        # query.name = "Completed tasks"
        # query.add("resolution", "Fixed")
        # query.add("issuetype", "Task")
        # query.set_project(self)

        # query = _Query(self.model, "resolved-tasks")
        # query.name = "Resolved tasks"
        # query.add("resolution", None, "is not")
        # query.add("issuetype", "Task")
        # query.set_project(self)

        # query = _Query(self.model, "resolved-with-empty-fix-version")
        # query.name = "Open resolved issues with empty fix version"
        # query.add("resolution", None, "is not")
        # query.add("fixVersion", None)
        # query.add("status", "Closed", "!=")
        # query.set_project(self)

        operation = _CreateIssue(self.model, "report-bug")
        operation.name = "Report bug"
        operation.issuetype = 1
        operation.set_project(self)

        operation = _CreateIssue(self.model, "request-feature")
        operation.name = "Request feature"
        operation.issuetype = 2
        operation.set_project(self)

        operation = _CreateIssue(self.model, "request-improvement")
        operation.name = "Request improvement"
        operation.issuetype = 4
        operation.set_project(self)

        operation = _CreateIssue(self.model, "add-task")
        operation.name = "Add task"
        operation.issuetype = 3
        operation.set_project(self)

        json_components = self.json_data["components"]
        json_versions = self.json_data["versions"]

        assignee = _Assignee(self.model, "aconway")
        assignee.name = "Alan Conway"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "astitcher")
        assignee.name = "Andrew Stitcher"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "chug")
        assignee.name = "Chuck Rolke"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "cliffjansen")
        assignee.name = "Cliff Jansen"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "eallen")
        assignee.name = "Ernie Allen"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "ganeshmurthy")
        assignee.name = "Ganesh Murthy"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "gemmellr")
        assignee.name = "Robbie Gemmell"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "gsim")
        assignee.name = "Gordon Sim"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "justi9")
        assignee.name = "Justin Ross"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "kgiusti")
        assignee.name = "Ken Giusti"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "mgoulish")
        assignee.name = "Mick Goulish"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "pmoravec")
        assignee.name = "Pavel Moravec"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "rajith")
        assignee.name = "Rajith Attapattu"
        assignee.set_project(self)

        assignee = _Assignee(self.model, "tedross")
        assignee.name = "Ted Ross"
        assignee.set_project(self)
        
        for json_component in json_components:
            component = _Component(self.model, json_component["id"])
            component.name = json_component["name"]
            component.description = json_component.get("description")
            component.set_project(self)

            for query in self.queries:
                copy = query.copy()
                copy.set_component(component)

            for operation in self.operations:
                copy = operation.copy()
                copy.set_component(component)

        for json_version in json_versions:
            version = _Version(self.model, json_version["id"])
            version.name = json_version["name"]
            version.description = json_version.get("description")
            version.release_date = json_version.get("release_date")
            version.set_project(self)

            for query in self.queries:
                copy = query.copy()
                copy.set_version(version)

            for operation in self.operations:
                copy = operation.copy()
                copy.set_version(version)

        for assignee in self.assignees:
            for query in self.queries:
                copy = query.copy()
                copy.set_assignee(assignee)

    def get_jira_url(self):
        return "{}/browse/{}".format(self.model.base_url, self.key)

    def pretty_print(self):
        _pprint.pprint(self.json_data)

class _Query(_ModelObject):
    def __init__(self, model, id):
        super(_Query, self).__init__(model, id)

        self.project = None
        self.component = None
        self.version = None
        self.assignee = None

        self.exprs = list()

    def copy(self):
        other = super(_Query, self).copy()
        other.project = self.project
        other.component = self.component
        other.version = self.version
        other.exprs = list(self.exprs)

        return other

    def set_project(self, project):
        self.project = project
        self.project.queries.append(self)

    def set_component(self, component):
        self.component = component
        self.component.queries.append(self)

    def set_version(self, version):
        self.version = version
        self.version.queries.append(self)

    def set_assignee(self, assignee):
        self.assignee = assignee
        self.assignee.queries.append(self)

    def add(self, name, value, operator=None):
        self.exprs.append((name, operator, value))

    def get_url(self):
        assert self.project is not None

        exprs = list(self.exprs)

        if self.component is not None:
            exprs.append(["component", "=", self.component.name])

        if self.version is not None:
            exprs.append(["fixVersion", "=", self.version.name])

        if self.assignee is not None:
            exprs.append(["assignee", "=", self.assignee.id])

        exprs.append(["project", "=", self.project.key])

        jql_exprs = list()

        for expr in exprs:
            name, operator, value = expr
            operator = self.marshal_operator(operator, value)
            value = self.marshal_value(value)

            jql_exprs.append("{} {} {}".format(name, operator, value))

        jql = " and ".join(jql_exprs)
        jql = _urllib.quote_plus(jql)

        return "{}/issues/?jql={}".format(self.model.base_url, jql)

    def marshal_operator(self, operator, value):
        if operator is None:
            if value is None:
                return "is"
            elif _is_sequence(value):
                return "in"
            else:
                return "="

        return operator

    def marshal_value(self, value):
        if _is_sequence(value):
            items = [self.marshal_scalar_value(x) for x in value]
            return "({})".format(", ".join(items))

        return self.marshal_scalar_value(value)

    def marshal_scalar_value(self, value):
        if value is None:
            return "EMPTY"
        elif isinstance(value, basestring):
            return "\"{}\"".format(value)

class _Operation(_ModelObject):
    def __init__(self, model, id):
        super(_Operation, self).__init__(model, id)

        self.project = None
        self.component = None
        self.version = None

    def copy(self):
        other = super(_Operation, self).copy()
        other.project = self.project
        other.component = self.component
        other.version = self.version

        return other

    def set_project(self, project):
        self.project = project
        self.project.operations.append(self)

    def set_component(self, component):
        self.component = component
        self.component.operations.append(self)

    def set_version(self, version):
        self.version = version
        self.version.operations.append(self)

class _CreateIssue(_Operation):
    def __init__(self, model, id):
        super(_CreateIssue, self).__init__(model, id)

        self.name = None
        self.issuetype = None

    def copy(self):
        other = super(_CreateIssue, self).copy()
        other.name = self.name
        other.issuetype = self.issuetype

        return other

    def get_url(self):
        path = "secure/CreateIssueDetails!init.jspa"

        args = list()

        args.append("pid={}".format(self.project.id))
        args.append("issuetype={}".format(self.issuetype))
        args.append("priority=3")
        args.append("summary=[Enter%20a%20brief%20description]")

        if self.component is not None:
            args.append("components={}".format(self.component.id))

        if self.version is not None:
            args.append("fixVersions={}".format(self.version.id))

        args = "&".join(args)

        return "{}/{}?{}".format(self.model.base_url, path, args)

class _Component(_ModelObject):
    def __init__(self, model, id):
        super(_Component, self).__init__(model, id)

        self.project = None

        self.queries = list()
        self.operations = list()

    def set_project(self, project):
        self.project = project
        self.project.components.append(self)
        self.project.components_by_id[self.id] = self

    def get_jira_url(self):
        return "{}/browse/{}/component/{}".format \
            (self.model.base_url, self.project.key, self.id)

class _Version(_ModelObject):
    def __init__(self, model, id):
        super(_Version, self).__init__(model, id)

        self.project = None
        self.release_date = None

        self.queries = list()
        self.operations = list()

    def set_project(self, project):
        self.project = project
        self.project.versions.append(self)
        self.project.versions_by_id[self.id] = self

    def get_jira_url(self):
        return "{}/browse/{}/fixforversion/{}".format \
            (self.model.base_url, self.project.key, self.id)

class _Assignee(_ModelObject):
    def __init__(self, model, id):
        super(_Assignee, self).__init__(model, id)

        self.queries = list()
        self.operations = list()

    def set_project(self, project):
        self.project = project
        self.project.assignees.append(self)
        self.project.assignees_by_id[self.id] = self

    def get_jira_url(self):
        return "{}/secure/ViewProfile.jspa?name={}".format \
            (self.model.base_url, self.id)

def _is_sequence(value):
    return not isinstance(value, basestring) and isinstance \
        (value, _collections.Sequence)
