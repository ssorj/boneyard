from ptolemy.common.server import *
from ptolemy.common.web import *

from wicket import *

log = logging.getLogger("ptolemy.consoleserver.web")

class WebThread(ServerThread):
    def __init__(self, server):
        super(WebThread, self).__init__(server, "web")

        path = os.path.join(self.server.home, "resources")
        self.app = WebApplication(self.server.model, path)

    def do_run(self):
        try:
            # They mean run forever
            self.app.start()
        except KeyboardInterrupt:
            self.app.stop()

class WebApplication(WicketApplication):
    def __init__(self, model, resources_path):
        super(WebApplication, self).__init__()

        self.model = model
        self.resources_path = resources_path

        self.html_page_template = _html_page_template

        overview = OverviewPage(self)
        self.pages_by_name["overview"] = overview
        self.pages_by_name[""] = overview

        path = self.resources_path
        self.pages_by_name["resource"] = ResourcePage(self, path)

        self.pages_by_name["project"] = ProjectPage(self)
        self.pages_by_name["branch"] = BranchPage(self)
        self.pages_by_name["cycle"] = CyclePage(self)
        self.pages_by_name["harness"] = HarnessPage(self)

class OverviewPage(HtmlPage):
    @classmethod
    def get_href(cls, arg):
        return "overview"

    @classmethod
    def get_title(cls, arg):
        return "Overview"

    def process(self, session):
        session.model = self.app.model

    def render_title(self, session):
        return self.get_title(session.model)

    def render_navigation(self, session):
        return html_list((self.get_link(session.model),))

    def render_content(self, session):
        elems = list()

        elems.append(self.render_projects(session))
        elems.append(self.render_harnesses(session))

        return "".join(elems)

    def render_projects(self, session):
        items = list()

        fn = lambda x: x.name
        projects = sorted(session.model.projects_by_name.values(), key=fn)

        for project in projects:
            items.append(ProjectPage.get_link(project))

        return html_section(html_list(items), "Projects")

    def render_harnesses(self, session):
        items = list()

        fn = lambda x: x.domain_name
        harnesses = sorted(session.model.harnesses_by_id.values(), key=fn)

        for harness in harnesses:
            href = "harness?%s" % harness.short_id
            text = harness.domain_name
            items.append(HarnessPage.get_link(harness))

        return html_section(html_list(items), "Harnesses")

class ProjectPage(HtmlPage):
    @classmethod
    def get_href(cls, project):
        return "project?%s" % project.name

    @classmethod
    def get_title(cls, project):
        return "Project %s" % project.name

    def process(self, session):
        project_name = session.env["QUERY_STRING"]
        session.project = self.app.model.projects_by_name[project_name]

    def render_title(self, session):
        return self.get_title(session.project)

    def render_navigation(self, session):
        items = list()

        items.append(OverviewPage.get_link(session.project.model))
        items.append(self.get_link(session.project))

        return html_list(items)

    def render_content(self, session):
        return self.render_branches(session)

    def render_branches(self, session):
        items = list()

        trunk = session.project.branches_by_name.get("trunk")

        if trunk:
            items.append(html_link("branch?%s" % trunk.key, trunk.name))

        for branch_name in sorted(session.project.branches_by_name):
            branch = session.project.branches_by_name[branch_name]

            if branch is trunk:
                continue

            items.append(html_link("branch?%s" % branch.key, branch.name))

        return html_section(html_list(items), "Branches")

class BranchPage(HtmlPage):
    @classmethod
    def get_href(cls, branch):
        return "branch?%s" % branch.key

    @classmethod
    def get_title(cls, branch):
        return "Branch %s" % branch.name

    def process(self, session):
        branch_key = session.env["QUERY_STRING"]
        session.branch = self.app.model.branches_by_key[branch_key]

    def render_title(self, session):
        return self.get_title(session.branch)

    def render_navigation(self, session):
        items = list()

        items.append(OverviewPage.get_link(session.branch.project.model))
        items.append(ProjectPage.get_link(session.branch.project))
        items.append(self.get_link(session.branch))

        return html_list(items)

    def render_content(self, session):
        return self.render_cycles(session)

    def render_cycles(self, session):
        rows = list()

        for env in sorted(session.branch.last_cycle_by_environment):
            try:
                cycle = session.branch.last_cycle_by_environment[env]
            except KeyError:
                continue

            rows.append(self.render_cycle_row(session, cycle))

        args = "", "Cycle", "Revision", "Time", "Status"
        headers = "<tr><th>%s</th></tr>" % "</th><th>".join(args)

        args = headers, "".join(rows)
        table = "<table><thead>%s</thead><tbody>%s</tbody></table>" % args

        return html_section(table, "Cycles")

    def render_cycle_row(self, session, cycle):
        columns = list()

        columns.append("<th>%s</th>" % str(cycle.harness.environment))

        args = cycle.short_id, cycle.short_id
        columns.append("<td><a href=\"cycle?%s\">%s</a></td>" % args)

        if cycle.revision is None:
            revision = "-"
        else:
            revision = cycle.revision

        columns.append("<td>%s</td>" % revision)
        
        time = cycle.end_time or cycle.start_time
        time = fmt_local_unixtime_brief(time)
        columns.append("<td>%s</td>" % time)

        status = cycle.status_message
        columns.append("<td>%s</td>" % status)

        return "<tr>%s</tr>" % "".join(columns)

class CyclePage(HtmlPage):
    @classmethod
    def get_href(cls, cycle):
        return "cycle?%s" % cycle.short_id

    @classmethod
    def get_title(cls, cycle):
        return "Cycle %s" % cycle.short_id

    def process(self, session):
        cycle_id = session.env["QUERY_STRING"]
        session.cycle = self.app.model.cycles_by_short_id[cycle_id]

    def render_title(self, session):
        return self.get_title(session.cycle)

    def render_navigation(self, session):
        items = list()

        items.append(OverviewPage.get_link(session.cycle.branch.project.model))
        items.append(ProjectPage.get_link(session.cycle.branch.project))
        items.append(BranchPage.get_link(session.cycle.branch))
        items.append(self.get_link(session.cycle))

        return html_list(items)

    def render_content(self, session):
        elems = list()

        elems.append(self.render_attributes(session))
        elems.append(self.render_test_results(session))

        return "".join(elems)

    def render_attributes(self, session):
        cycle = session.cycle

        project_href = ProjectPage.get_href(cycle.branch.project)

        attrs = (
            ("ID", cycle.id),
            ("Project", html_link(project_href, cycle.branch.project.name)),
            ("Harness", cycle.harness.id),
            ("URL", html_link(cycle.url)),
            ("Branch", cycle.branch.key),
            ("Revision", cycle.revision),
            ("Start time", fmt_local_unixtime(cycle.start_time)),
            ("End time", fmt_local_unixtime(cycle.end_time)),
            ("Status", "%i [%s]" % (cycle.status_code, cycle.status_message)),
            )

        rows = list()

        for name, value in attrs:
            args = name, value
            rows.append("<tr><th>%s</th><td>%s</td></tr>" % args)

        table = "<table><tbody>%s</tbody></table>" % "".join(rows)
        return html_section(table, "Attributes")

    def render_test_results(self, session):
        return html_section("XXX", "Test results")

class HarnessPage(HtmlPage):
    @classmethod
    def get_href(cls, harness):
        return "harness?%s" % harness.short_id

    @classmethod
    def get_title(cls, harness):
        return "Harness %s" % harness.domain_name

    def process(self, session):
        harness_id = session.env["QUERY_STRING"]
        session.harness = self.app.model.harnesses_by_short_id[harness_id]

    def render_title(self, session):
        return self.get_title(session.harness)

    def render_navigation(self, session):
        items = list()

        items.append(OverviewPage.get_link(session.harness.model))
        items.append(self.get_link(session.harness))

        return html_list(items)

    def render_content(self, session):
        return "XXX"

_html_page_template = \
"""<?xml version="1.0"?>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <title>Ptolemy - ${title}</title>
    <link rel="stylesheet" type="text/css" href="resource?main.css"/>
  </head>
  <body>
    <div id="navigation">${navigation}</div>
    <div id="main">
      <h1>${title}</h1>
      ${content}
    </div>
  </body>
</html>"""
