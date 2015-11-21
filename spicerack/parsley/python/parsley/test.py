import logging
import sys
import os

from fnmatch import fnmatchcase
from random import randint
from traceback import print_exc, extract_tb
from datetime import datetime
from threading import Thread
from time import clock, sleep, time

log = logging.getLogger("parsley.test")

class TestHarness(object):
    def __init__(self, test):
        self.test = test
        self.test.harness = self

        self.tests = list()

        self.include = list()
        self.exclude = list()

        self.initialized = False

    def init(self):
        assert not self.initialized
        assert isinstance(self.test, Test)

        self.test.init()

        self.initialized = True

    def run(self):
        assert self.initialized
        assert isinstance(self.test, Test)

        session = TestSession(self)

        self.test.run(session)

        return session

class TestSession(object):
    def __init__(self, harness):
        self.harness = harness
        self.id = short_id()

        self.test_calls_by_test = dict()

    def report(self, out=sys.stdout):
        enabled = 0
        disabled = 0
        passed = 0
        failed = 0
        skipped = 0

        failed_calls = list()

        out.write("Tests:")
        out.write(os.linesep)
        out.write(os.linesep)

        for test in self.harness.tests:
            status = None
            elaboration = None

            if test.enabled:
                enabled += 1

                call = self.test_calls_by_test.get(test)

                if call:
                    if call.exception:
                        failed += 1
                        failed_calls.append(call)
                        status = "failed"
                        elaboration = call.get_exception_text()
                    else:
                        passed += 1
                        status = "passed"
                else:
                    skipped += 1
                    status = "skipped"
            else:
                disabled += 1
                status = "disabled"

            out.write("  %-38s %s" % (test.path, status))
            out.write(os.linesep)

            if elaboration:
                out.write("    %s" % elaboration)
                out.write(os.linesep)

        out.write(os.linesep)

        out.write("Failures:")
        out.write(os.linesep)
        out.write(os.linesep)

        if failed_calls:
            for call in failed_calls:
                out.write("  %s: %s" % \
                              (call.test.path, call.get_exception_text()))
                out.write(os.linesep)
                out.write(os.linesep)

                for spec in extract_tb(call.traceback):
                    file, line, func, text = spec
                    out.write("    %s:%i:%s" % spec[:3])
                    out.write(os.linesep)
                    out.write("      %s" % spec[3])
                    out.write(os.linesep)

                out.write(os.linesep)
        else:
            out.write("  None")
            out.write(os.linesep)
            out.write(os.linesep)

        out.write("Summary:")
        out.write(os.linesep)
        out.write(os.linesep)

        out.write("  %i tests" % len(self.harness.tests))
        out.write(os.linesep)

        out.write("    %i disabled" % disabled)
        out.write(os.linesep)

        out.write("    %i enabled" % enabled)
        out.write(os.linesep)

        out.write("      %i passed" % passed)
        out.write(os.linesep)

        out.write("      %i failed" % failed)
        out.write(os.linesep)

        out.write("      %i skipped" % skipped)
        out.write(os.linesep)
        out.write(os.linesep)

class Test(object):
    def __init__(self, name, parent):
        assert isinstance(name, str)

        if parent:
            assert isinstance(parent, Test)

        self.name = name
        self.parent = parent
        self.children = list()
        self.ancestors = list()

        self.harness = None
        self.path = None
        self.enabled = None

        if parent:
            self.parent.children.append(self)

    def init(self):
        log.debug("Initializing %s", self)

        if self.parent is None:
            self.path = self.name
        else:
            self.harness = self.parent.harness
            self.path = "%s.%s" % (self.parent.path, self.name)

            ancestor = self.parent

            while ancestor:
                self.ancestors.append(ancestor)
                ancestor = ancestor.parent

        self.harness.tests.append(self)

        for pattern in self.harness.include:
            if fnmatchcase(self.path, pattern):
                self.enabled = True

                for ancestor in self.ancestors:
                    ancestor.enabled = True

                break

        for pattern in self.harness.exclude:
            if fnmatchcase(self.path, pattern):
                self.enabled = False

                break

        if not self.enabled:
            log.debug("%s is disabled", self)

        for child in self.children:
            child.init()

    def run(self, session):
        if not self.enabled:
            return

        log.debug("Running %s", self)

        call = TestCall(session, self)

        call.open()

        try:
            try:
                self.do_run(session)
            except Exception, e:
                call.exception = e
                call.traceback = sys.exc_info()[2]
        finally:
            call.close()

    def do_run(self, session):
        self.run_children(session)

    def run_children(self, session):
        for child in self.children:
            child.run(session)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.path)

class TestCall(object):
    def __init__(self, session, test):
        self.session = session
        self.test = test
        self.exception = None
        self.traceback = None

        self.start = None
        self.end = None

        self.session.test_calls_by_test[test] = self

    def open(self):
        self.start = clock()

    def close(self):
        self.end = clock()

    def get_exception_text(self):
        if self.exception:
            return str(self.exception)

class PassTest(Test):
    pass

class FailTest(Test):
    def do_run(self, session):
        raise Exception("!")

def short_id():
    return "%08x" % randint(0, sys.maxint)
