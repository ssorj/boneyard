from mint import *
from wooly import *

from cumin.test import *

import main

from cumin.model import Pool
from wooly import Session

class GridTest(Test):
    def __init__(self, name, parent):
        super(GridTest, self).__init__(name, parent)

        self.pool = None
        self.scheduler = None

        SubmissionTest("Submission", self)

    def do_run(self, session):
        collector = check_get_object(Collector)

        self.pool = Pool(collector.Pool)

        self.scheduler = check_get_object(Scheduler)

        super(GridTest, self).do_run(session)

class SubmissionTest(Test):
    def __init__(self, name, parent):
        super(SubmissionTest, self).__init__(name, parent)

        self.submission = None

    def do_run(self, session):
        s = MainPageSession(self.harness)

        task = main.module.submission_add

        ns = task.enter(s, self.parent.pool)

        check_render(ns)

        task.form.description.set(ns, session.id)
        task.form.command.set(ns, "/bin/sleep 5m")

        check_submit_form(ns, task.form)

        self.submission = check_get_object(Submission, Name=session.id)

        super(SubmissionTest, self).do_run(session)
