from util import *

class PageProfile(object):
    def __init__(self, page):
        self.page = page

        self.process_calls = list()
        self.render_calls = list()

        self.current_calls = list()

        self.urls = list()

    def compute_times(self):
        for calls in (self.process_calls, self.render_calls):
            for call in calls:
                call.compute_time()

        for calls in (self.process_calls, self.render_calls):
            for call in calls:
                call.compute_self_time()

    def collate_render_times(self, render_times_by_widget):
        for call in self.render_calls:
            render_times_by_widget[call.widget].append(call.self_time)

    def print_results(self):
        render_times_by_widget = defaultdict(list)

        self.collate_render_times(render_times_by_widget)

        row = "%-100s  %8.3f  %8.3f  %8.3f  %8i  %8.3f"

        print "-" * 80
        #print row % ("Class", "Min", "Max", "Avg", "Count", "Total")

        for widget in sorted(render_times_by_widget):
            times = render_times_by_widget[widget]

            count = len(times)
            total = sum(times)
            avg = total / float(count)

            print row % (widget, min(times), max(times), avg, count, total)

    def print_process_render_asymmetry(self):
        processed = set()
        rendered = set()

        for call in self.process_calls:
            processed.add(call.widget)

        for call in self.render_calls:
            rendered.add(call.widget)

        for widget in processed.difference(rendered):
            print "Warning: %s was processed but not rendered" % widget

        for widget in rendered.difference(processed):
            print "Warning: %s was rendered but not processed" % widget

    def print_stack_trace(self, writer=sys.stdout):
        for call in self.current_calls:
            writer.write("  in %s\n" % call)

    def print_process_calls(self):
        if self.process_calls:
            self.__print_calls(self.process_calls[-1])

    def print_render_calls(self):
        if self.render_calls:
            self.__print_calls(self.render_calls[-1])

    def __print_calls(self, root):
        def visit(call, depth):
            print "  " * depth,

            if call.time is None:
                time = "[incomplete]"
            else:
                time = "%.3f" % call.time

            print "%s (%s)" % (call.widget, time)

            for callee in call.callees:
                visit(callee, depth + 1)

        visit(root, 0)

class WidgetCall(object):
    def __init__(self, profile, widget, args):
        self.profile = profile
        self.widget = widget
        self.args = args

        self.profile

        self.caller = None
        self.callees = list()
        
        if self.profile.current_calls:
            self.caller = self.profile.current_calls[-1]
            self.caller.callees.append(self)

        self.start = None
        self.end = None

        self.time = None
        self.self_time = None

    def write(self, writer):
        writer.write(str(self.widget))
        writer.write(" [%i]" % id(self))

    def compute_time(self):
        assert self.start is not None
        assert self.end is not None
        assert self.start < self.end

        self.time = (self.end - self.start) * 1000

    def compute_self_time(self):
        assert self.time is not None

        if self.callees:
            callee_time = sum([x.time
                               for x in self.callees
                               if x.time is not None])

            self.self_time = self.time - callee_time
        else:
            self.self_time = self.time

    def __repr__(self):
        return "%s(%s,%s)" % (self.__class__.__name__, self.widget, self.args)

class ProcessCall(WidgetCall):
    def do(self, session):
        self.profile.current_calls.append(self)

        self.start = time.time()

        self.widget.do_process(session)

        self.end = time.time()

        self.profile.current_calls.pop()
        self.profile.process_calls.append(self)

class RenderCall(WidgetCall):
    def do(self, session):
        self.profile.current_calls.append(self)

        self.start = time.time()

        result = self.widget.do_render(session)

        self.end = time.time()

        if self.widget.parent:
            name = self.widget.__repr__()
            fmt = "<!-- \nopen: %s\n-->%s<!-- \nclose: %s\n-->"

            if result is None:
                result = ""

            result = fmt % (name, result, name)

        self.profile.current_calls.pop()
        self.profile.render_calls.append(self)

        return result
