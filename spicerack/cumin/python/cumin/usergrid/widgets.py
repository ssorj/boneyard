from wooly import *
from wooly.widgets import *

import cumin.grid

from cumin.model import CuminStatistic
from cumin.parameters import *
from cumin.widgets import *
from cumin.util import *
from cumin.grid.submission import *
from cumin.grid.slot import *

from wooly.widgets import Link

from model import *
from widgets import *

import main

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.usergrid.widgets")

class MainPage(CuminPage, ModeSet):
    def __init__(self, app, name):
        super(MainPage, self).__init__(app, name)

        self.main = MainView(app, "main", self.user)
        self.add_mode(self.main)
        self.set_default_frame(self.main)

        self.page_html_class = "Cumin"

    def render_title(self, session):
        return self.get_title(session)

    def get_title(self, session):
        return "Grid User"

class MainView(CuminMainView):
    def __init__(self, app, name, user):
        super(MainView, self).__init__(app, name)

        self.overview = OverviewFrame(app, "overview", user)
        self.add_tab(self.overview)

        self.submissions = SubmissionsFrame(app, "submissions", user)
        self.add_tab(self.submissions)

class OverviewFrame(CuminFrame):
    def __init__(self, app, name, user):
        super(OverviewFrame, self).__init__(app, name)

        # XXX temp hack. these are 
        # not used but needed for SubmissionAdd ObjectFrameTask
        self.tasks = list()
        self.id = Attribute(app, "id")
        self.id.default = 0
        self.add_attribute(self.id)

        self.view = OverviewView(app, "view", user, self)
        self.add_mode(self.view)

    def render_title(self, session):
        return "Overview"

class OverviewView(Widget):
    def __init__(self, app, name, user, frame):
        super(OverviewView, self).__init__(app, name)

        self.stats = UserJobStatSet(app, "jobs", user)
        self.add_child(self.stats)

        link = TaskLink(app, "job_submit", app.grid.job_submit)
        self.add_child(link)

        link = TaskLink(app, "dag_job_submit", app.grid.dag_job_submit)
        self.add_child(link)

        link = TaskLink(app, "vm_job_submit", app.grid.vm_job_submit)
        self.add_child(link)

        # XXX
        # task = SubmissionVMAdd(app)
        # self.vm_link = ObjectTaskLink(app, "submissionvmadd", task)
        # self.add_child(self.vm_link)

        # task = SubmissionDagAdd(app, frame)
        # self.dag_link = ObjectTaskLink(app, "submissiondagadd", task)
        # self.add_child(self.dag_link)

class SubmissionsFrame(CuminFrame):
    def __init__(self, app, name, user):
        super(SubmissionsFrame, self).__init__(app, name)

        self.view = UserSubmissionSelector(app, "view", user)
        self.add_mode(self.view)

        self.submission = SubmissionFrame(app, "submission", 
                                          check_viewable=True)
        self.add_mode(self.submission)

    def render_title(self, session):
        return "Submissions"

class UserSubmissionSelector(SubmissionSelector):
    def __init__(self, app, name, user):
        super(UserSubmissionSelector, self).__init__(app, name)

        self.user = user

        cls = self.app.model.com_redhat_cumin.User

        self.add_filter(self.user, self.cls.Owner, cls.name)

        frame = "main.submissions.submission"
        col = self.UserSubmissionObjectLinkColumn(app, "name", self.cls.Name, self.cls._id, frame)
        self.insert_column(0, col)
        self.add_search_filter(col)

        link = TaskLink(app, "job_submit", app.grid.job_submit)
        self.links.add_child(link)

        link = TaskLink(app, "dag_job_submit", app.grid.dag_job_submit)
        self.links.add_child(link)

        link = TaskLink(app, "vm_job_submit", app.grid.vm_job_submit)
        self.links.add_child(link)

        self.enable_csv_export(user)
        
    class UserSubmissionObjectLinkColumn(ObjectLinkColumn):      
        def render_cell_content(self, session, record):
            retval = len(record) > 0 and record[self.field.index] or ""
            if(len(record[self.field.index]) > 50):
                retval = record[self.field.index][:50] + "..."  #indicate that we truncated the name
            return retval

class UserJobStatSet(NewStatSet):
    def __init__(self, app, name, user):
        super(UserJobStatSet, self).__init__(app, name)

        stat = self.RunningJobs("running")
        self.stats.append(stat)

        stat = self.IdleJobs("idle")
        self.stats.append(stat)

        stat = self.HeldJobs("held")
        self.stats.append(stat)

        self.load = LoadUserJobStats(app, user)

    def get_values(self, session):
        return self.load.execute(session).fetchone()

    class RunningJobs(CuminStatistic):
        def get_title(self, session):
            return "Running"

    class IdleJobs(CuminStatistic):
        def get_title(self, session):
            return "Idle"

    class HeldJobs(CuminStatistic):
        def get_title(self, session):
            return "Held"
