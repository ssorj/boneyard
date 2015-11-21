from ptolemy.common.process import *
from util import *

log = logging.getLogger("ptolemy.harness.script")

class Script(object):
    def __init__(self, path):
        self.path = path

        self.warn_duration = None
        self.max_duration = None

    def exists(self):
        return os.path.exists(self.path)

    def warn(self, proc):
        pass

    def run(self, output_path, args=[]):
        output_file = open(output_path, "w")
        try:
            return self.run_file(output_file, args)
        finally:
            output_file.close()
        
    def run_file(self, output, args=[]):
        proc = UnixProcess(self.path)
        proc.output = output
        proc.args = args

        proc.start()
        self.add_running_process(proc)

        try:
            self.monitor_process(proc)
        finally:
            self.remove_running_process(proc)
            proc.stop()

        return proc

    def add_running_process(self, proc):
        pass

    def remove_running_process(self, proc):
        pass

    def monitor_process(self, proc):
        start_time = time.time()
        warn_time = None
        stop_time = None

        if self.warn_duration:
            warn_time = start_time + self.warn_duration

        if self.max_duration:
            stop_time = start_time + self.max_duration

        while proc.running():
            time.sleep(1)

            #log.debug("Tick")

            now = time.time()

            if warn_time and now > warn_time:
                log.debug("%s overran warn time", self)

                warn_time = None
                self.warn(proc)

            if stop_time and now > stop_time:
                log.debug("%s overran max time; stopping it", self)

                stop_time = None
                proc.stop()

    def __repr__(self):
        args = self.__class__.__name__, self.path
        return "%s(%s)" % args

if __name__ == "__main__":
    add_logging("ptolemy", "debug", sys.stdout)

    now = time.time()

    script = Script("/usr/bin/vmstat")
    script.warn_duration = 3
    script.max_duration = 5

    script.run("/dev/stdout", ["1"])
