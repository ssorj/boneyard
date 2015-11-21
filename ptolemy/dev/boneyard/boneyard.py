def compute_dir_digest(path):
    hash = sha.new()
    time = 0

    for dpath, dnames, fnames in os.walk(path):
        dinfo = os.stat(dpath)
        hash.update(dpath)
        # We ignore dir change times
        #time = max(time, dinfo[stat.ST_MTIME], dinfo[stat.ST_CTIME])

        for fname in fnames:
            fpath = os.path.join(dpath, fname)

            try:
                finfo = os.stat(fpath)
                hash.update(fpath)
                time = max(time, finfo[stat.ST_MTIME], finfo[stat.ST_CTIME])
            except OSError:
                pass
            
        for dname in (".svn", "CVS"):
            if dname in dnames:
                dnames.remove(dname)

    return hash.hexdigest() + " " + str(time)


class Project(object):
    def __init__(self, model, name):
        self.model = model
        self.name = name
        self.path = os.path.join \
            (self.model.harness.path, "projects", self.name)
        self.uri = "%s/%s" % (self.model.harness.name, self.name)

        self.config = ProjectConfig(self)

        self.mail_addrs = set()

        self.source_path = None
        self.install_path = None

        self.requires = None
        self.owners = None

        self.cycles_path = os.path.join \
            (self.model.harness.cycles_path, self.name)
        self.cycles = list()
        self.cycles_by_id = dict()

        self.current_cycle = None
        self.previous_cycle = None

        self.enqueue_time = None

        self.init_script = Script(self, "init")
        self.update_script = Script(self, "update")
        self.build_script = Script(self, "build")
        self.test_script = Script(self, "test")

        self.timeout_script = Script(self, "timeout")

    def add_cycle(self, cycle):
        self.cycles.append(cycle)
        self.cycles_by_id[cycle.id] = cycle

    def load(self):
        log.debug("Loading %s", self)

        self.config.load()

        source = self.config.source.get()
        self.source_path = os.path.join \
            (self.model.harness.sources_path, source)

        install = self.config.install.get()
        self.install_path = os.path.join \
            (self.model.harness.installs_path, install)

        init_path(self.install_path)
        init_path(self.cycles_path)

        self.owners = self.config.owners.get()

        for id in sorted(os.listdir(self.cycles_path),
                         cmp=lambda x, y: int(x) - int(y)):
            try:
                cycle = Cycle(self, int(id))
            except TypeError:
                pass

            try:
                cycle.load()
            except:
                log.exception("Failure loading %s", cycle)
                continue

            self.add_cycle(cycle)

        log.info("Loaded %s with %i cycles", self, len(self.cycles))

    def init(self):
        log.debug("Initializing %s", self)

        self.requires = [self.model.projects_by_name[x]
                         for x in self.config.requires.get()]

        for cycle in self.cycles:
            cycle.init()

    def find_cycle(self, start, statuses=None):
        if statuses:
            i = len(self.cycles) - start

            while i > 0:
                i -= 1
                cycle = self.cycles[i]

                if cycle.status in statuses:
                    return cycle
        else:
            return self.cycles[-(1 + start)]

    def last_completed_cycle(self):
        for last in reversed(self.cycles):
            if last.status and last.status != last.RUNNING:
                return last

    def last_noteworthy_cycle(self):
        for last in reversed(self.cycles):
            if last.status in (Cycle.RUNNING, last.FAILED, last.OK):
                return last

    def required_projects(self):
        reqs = set()

        def visit(proj):
            reqs.add(proj)

            for req in proj.requires:
                visit(req)

        for req in self.requires:
            visit(req)

        return reqs

    def run(self, request):
        if self in request.cycles_by_project:
            log.debug("%s has already run", self)

            return request.cycles_by_project[self]

        # XXX Check here if we want to skip, instead of getting into a
        # new cycle

        id = 1

        if self.current_cycle:
            id = self.current_cycle.id + 1

        cycle = Cycle(self, id)

        if request.deps:
            for project in self.requires:
                required = project.run(request)
                cycle.requires.append(required)

        request.cycles.append(cycle)
        request.cycles_by_project[self] = cycle

        log.info("Processing %s", cycle)

        if not os.path.exists(cycle.path):
            os.makedirs(cycle.path)

        try:
            cycle.run(request)
        finally:
            cycle.save()

        log.info("Processed %s -> %s", cycle, cycle.status_text())

        if self.model.harness.debug:
            summary = CycleSummary(cycle)

            print "*** %s ***" % summary.get_title()
            print
            print summary.get_body()

# XXX
#        if self.newsworthy(cycle):
#            self.server.mail_thread.enqueue(cycle)
#            self.server.notify_thread.enqueue(cycle)

        return cycle

    def newsworthy(self, cycle):
        # Only notify when status really changes

        # XXX Consider also looking at exit codes and signals

        log.debug("Checking newsworthiness of %s", cycle)

        last = self.find_cycle(1, (Cycle.FAILED, Cycle.OK))

        log.debug("Comparing to previous %s", last)

        if cycle.status is Cycle.OK:
            if last and last.status is Cycle.FAILED:
                log.info("%s fixed", self)

                return True
        elif cycle.status is Cycle.FAILED:
            if last is None or last.status is Cycle.OK:
                log.info("%s is newly failing", self)

                return True
            elif last.status == Cycle.FAILED \
                    and last.script_name != cycle.script_name:
                log.info("%s has failed again, in a different script", self)

                return True
            else:
                log.info("%s has failed again, in the same script", self)

        return False

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.name)

class Cycle(object):
    DISABLED = "disabled"
    FAILED = "failed"
    NO_CHANGES = "no_changes"
    OK = "ok"
    RUNNING = "running"
    SKIPPED = "skipped"

    verbs = {
        "init": ("initializing", "initialized"),
        "update": ("updating", "updated"),
        "build": ("building", "built"),
        "test": ("testing", "tested"),
        "timeout": ("timing out", "timed out")
        }

    statuses = {
        NO_CHANGES: "no changes",
        }

    def __init__(self, project, id):
        self.project = project
        self.id = id
        self.path = os.path.join(self.project.cycles_path, str(self.id))
        self.uri = "%s/%i" % (self.project.uri, self.id)

        self.requires = list()

        self.revision = None
        self.changes = list()

        self.props = Properties(self.path, "props")

        self.status = None

        self.start_time = None
        self.end_time = None

        self.running_scripts = list()

        self.script_name = None
        self.script_exit_code = None
        self.script_exit_signal = None
        self.script_output = None

        self.project.cycles.append(self)
        self.project.cycles_by_id[self.id] = self

        self.project.previous_cycle = self.project.current_cycle
        self.project.current_cycle = self

    def required_cycles(self):
        reqs = set()

        def visit(cycle):
            reqs.add(cycle)

            for req in cycle.requires:
                visit(req)

        for req in self.requires:
            visit(req)

        return reqs

    def status_text(self):
        if self.status == self.RUNNING:
            if self.running_scripts:
                text = self.verbs[self.running_scripts[-1].name][0]
            else:
                text = "interrupted"
        elif self.status == self.FAILED:
            text = "%s failed" % self.script_name
        else:
            text = self.statuses.get(self.status, self.status)

        return text

    # XXX ugh, don't like this
    def message(self):
        msg = CycleMessage(self)
        self.set_message_headers(msg.headers)
        return msg

    def set_message_headers(self, headers):
        headers["id"] = self.id
        headers["revision"] = self.revision
        headers["status"] = self.status
        headers["status_text"] = self.status_text()
        headers["start_time"] = self.start_time
        headers["end_time"] = self.end_time

        # XXX uri url oh my

        headers["uri"] = self.uri

        if self.status == Cycle.FAILED:
            output = self.script_output

            # This is to deal with legacy data
            if output.startswith("/"):
                output = os.path.basename(output)

            headers["error_uri"] = "%s/%s" % (self.uri, output)

    def load_revision(self):
        try:
            self.revision = load(self.path, "revision").strip()
        except IOError:
            pass

    def load_changes(self):
        try:
            file = open(os.path.join(self.path, "changes"))

            try:
                for line in file.readlines():
                    try:
                        rev, user = line[:-1].split(" ", 1)
                        self.changes.append((rev, user))
                    except:
                        pass
            finally:
                file.close()
        except IOError:
            pass

    def load(self):
        log.debug("Loading %s", self)

        self.load_revision()
        self.load_changes()

        self.props.load()

        try:
            self.start_time = float(self.props["start_time"])
            self.end_time = float(self.props["end_time"])
        except KeyError:
            pass

        self.status = self.props.get("status")

        compat = self.props.get("error_script")
        self.script_name = self.props.get("script_name", compat)

        compat = self.props.get("error_code")
        self.script_exit_code = self.props.get("script_exit_code", compat)

        self.script_exit_signal = self.props.get("script_exit_signal")

        compat = self.props.get("error_output")
        self.script_output = self.props.get("script_output", compat)

    def init(self):
        pass

    def save(self):
        log.debug("Saving %s", self)

        if self.start_time:
            self.props["start_time"] = "%.6f" % self.start_time

        if self.end_time:
            self.props["end_time"] = "%.6f" % self.end_time

        self.props["status"] = self.status
        self.props["script_name"] = self.script_name
        self.props["script_exit_code"] = self.script_exit_code
        self.props["script_exit_signal"] = self.script_exit_signal
        self.props["script_output"] = self.script_output

        self.props.save()

    def delete(self):
        log.debug("Deleting %s", self)

        for root, dirs, files in os.walk(self.path, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

        os.rmdir(self.path)

        self.project.cycles.remove(self)
        del self.project.cycles_by_id[self.id]

        # XXX Also clean up current and previous refs, perhaps

    def setup_environment(self):
        last = self.project.last_completed_cycle()

        if last and last.revision:
            os.environ["LAST_REVISION"] = last.revision
        else:
            try:
                del os.environ["LAST_REVISION"]
            except KeyError:
                pass

        os.environ["PROJECT_PATH"] = self.project.path
        os.environ["SOURCE_PATH"] = self.project.source_path
        os.environ["INSTALL_PATH"] = self.project.install_path
        os.environ["CYCLE_PATH"] = self.path

    def skipped(self):
        for req in self.project.required_projects():
            last = req.last_noteworthy_cycle()

            if last:
                if last.status == self.FAILED:
                    if last.script_name != "test":
                        return True

                if last.status == self.DISABLED:
                    return True

        return False

    def changed(self):
        try:
            last = self.project.cycles[-2]

            if last.revision != self.revision:
                return True
        except IndexError:
            return True

        for req in self.project.required_projects():
            last = req.cycles[-1]

            if last.status == self.OK:
                return True

        return False

    def run(self, request):
        assert self.status is None
        assert self.project

        if self.skipped():
            self.status = self.SKIPPED
            return

        self.setup_environment()

        self.start_time = unixtime_now()

        self.status = self.RUNNING

        os.chdir(self.project.path)

        try:
            self.project.init_script.run(self)
            self.project.update_script.run(self)

            self.load_revision()
            self.load_changes()

            if self.changed() or request.force:
                self.project.build_script.run(self)
                self.project.test_script.run(self)

                self.status = self.OK
            else:
                self.status = self.NO_CHANGES
        except ScriptDisabled:
            self.status = self.DISABLED
        except ScriptFailed, e:
            self.status = self.FAILED

            self.script_name = e.script.name
            self.script_exit_code = e.process.exit_code
            self.script_exit_signal = e.process.exit_signal
            self.script_output = e.output

        self.end_time = unixtime_now()

    def __str__(self):
        return "%s(%s,%i)" % \
            (self.__class__.__name__, self.project.name, self.id)

class Script(object):
    def __init__(self, project, name):
        self.project = project
        self.name = name
        self.path = "%s.script" % os.path.join(self.project.path, self.name)
        self.common_path = "%s.script" % os.path.join \
            (self.project.model.harness.projects_path, "common", self.name)

    def check(self):
        pass # XXX Make sure the script looks okay

    def run(self, cycle):
        path = self.path

        if not os.path.isfile(path):
            path = self.common_path

            if not os.path.isfile(path):
                return

        log.debug("Starting %s", self.name)

        cycle.running_scripts.append(self)

        proc = UnixProcess(path)

        timeouts = [0]

        def handle_timeout():
            log.info("%s timed out (%i)", proc, timeouts[0])

            timeouts[0] += 1

            if timeouts[0] == 2:
                log.debug("Killing process %s", proc)

                proc.kill()
                proc.wait()

                return

            try:
                self.project.timeout_script.run(cycle)
            except ScriptException, e:
                log.exception(e)

            # XXX
            #self.project.server.mail_thread.enqueue(cycle)
            #self.project.server.notify_thread.enqueue(cycle)

            proc.deadline = unixtime_now() + 60 * 60

        proc.timeout_handler = handle_timeout
        proc.deadline = unixtime_now() + 60 * 60

        output = "%s.out" % self.name
        gzipped_output = "%s.gz" % output

        output_path = os.path.join(cycle.path, output)
        gzipped_output_path = os.path.join(cycle.path, gzipped_output)

        output_file = open(output_path, "w")

        try:
            proc.run(output_file)
        finally:
            output_file.close()

        log.debug("Finished %s -> %i %i", self.name,
                  proc.exit_code, proc.exit_signal)

        make_gzipped_copy(output_path, gzipped_output_path)

        os.remove(output_path)

        cycle.running_scripts.pop()

        if proc.exit_code == 64:
            raise ScriptDisabled(self)

        if proc.exit_code != 0 or proc.exit_signal != 0:
            raise ScriptFailed(self, proc, gzipped_output)

    def __str__(self):
        return "%s(%s,%s)" % \
            (self.__class__.__name__, self.project.name, self.name)

class ScriptException(Exception):
    def __init__(self, script, process=None, output=None):
        Exception.__init__(self)

        self.script = script
        self.process = process
        self.output = output

    def __str__(self):
        return "%s(%s)" % (self.__class__.__name__, self.script)

class ScriptDisabled(ScriptException):
    pass

class ScriptTimedOut(ScriptException):
    pass

class ScriptFailed(ScriptException):
    pass

class CycleSession(object):
    def __init__(self):
        self.force = False
        self.deps = True

        self.cycles = list()
        self.cycles_by_project = dict()

class CycleMessage(PtolemyMessage):
    def __init__(self, cycle):
        super(CycleMessage, self).__init__()

        self.cycle = cycle
