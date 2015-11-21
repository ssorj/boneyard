from xml.parsers.expat import ParserCreate

from server import ClientSession
from util import *
from wooly import Session, PageRedirect

class BenchmarkHarness(object):
    def __init__(self, app):
        self.app = app
        self.continue_on_error = False
        self.check_output = False
        self.print_output = False

        self.client_session = ClientSession()

        self.profiles = list()

    def visit(self, url, referer, depth):
        if depth > 2:
            raise Exception("Too many redirects")

        session = Session.unmarshal(self.app, url)
        session.client_session = self.client_session

        page = session.page

        profile = page.profile.get(session)
        self.profiles.append(profile)

        try:
            content = page.service(session)
            passed = True
        except PageRedirect:
            redirect = page.redirect.get(session)

            assert redirect

            return self.visit(redirect, url, depth + 1)
        except KeyboardInterrupt:
            raise
        except:
            print "Page failure"

            content = ""
            passed = False

            profile.print_stack_trace()

            print "Referer: %s" % referer

            if not self.continue_on_error:
                raise

        if self.print_output:
            self.print_output_with_line_numbers(content)

        if self.check_output:
            parser = ParserCreate()
            parser.Parse(content)

        return (content, profile, passed)

    def print_output_with_line_numbers(self, content):
        lines = content.split(os.linesep)

        print "-" * 80

        for i, line in enumerate(lines):
            print "%4i %s" % (i + 1, line)

        print "-" * 80

    def run(self, max_count=-1):
        urls = list()
        visited = set()
        times = list()

        passed = 0
        failed = 0

        count = 1
        referer = None
        url = ""

        while url is not None:
            visited.add(url)

            print "%i %s" % (count, url)

            start = time.time()

            content, profile, okay = self.visit(url, referer, 0)

            end = time.time()

            if okay:
                passed += 1
            else:
                failed += 1

            bytes = len(content)
            millis = (end - start) * 1000

            print "%i [%i bytes, %i millis]" % (count, bytes, millis)

            times.append(millis)

            #profile.print_process_render_asymmetry()
            #profile.compute_times()
            #profile.print_results()
            #profile.print_process_calls()
            #profile.print_render_calls()

            if count == max_count:
                break

            count += 1

            for purl in profile.urls:
                if purl not in visited:
                    urls.append((purl, url))

            if not urls:
                break

            url, referer = urls.pop()

        print 
        print "Passed: %i" % passed
        print "Failed: %i" % failed

        args = (sum(times) / float(len(times)), min(times), max(times))

        print "Times: Avg %.3f, Min %.3f, Max %.3f" % args

        print
        self.print_profile()

    def print_profile(self):
        render_times_by_widget = defaultdict(list)

        for profile in self.profiles:
            profile.compute_times()
            profile.collate_render_times(render_times_by_widget)

        head = "%-110s  %8s  %8s  %8s  %8s  %8s"

        print head % ("Widget", "Avg", "Min", "Max", "Count", "Total")

        row = "%-110s  %8.3f  %8.3f  %8.3f  %8i  %8.3f"

        records = list()

        for widget in render_times_by_widget:
            times = render_times_by_widget[widget]

            count = len(times)
            total = sum(times)
            avg = total / float(count)

            records.append((widget, avg, min(times), max(times), count, total))

        for i, record in enumerate(reversed(sorted_by_index(records, 5))):
            print row % record

            if i == 25:
                break

def truncate(string, length):
    if len(string) > length:
        return string[:length]
    else:
        return string

def sorted_by_index(seq, index):
    return sorted(seq, cmp, lambda x: x[index])
