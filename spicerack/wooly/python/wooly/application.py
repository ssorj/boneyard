from page import *
from resources import *
from util import *

log = logging.getLogger("wooly.application")

class Application(object):
    def __init__(self):
        self.pages = list()
        self.pages_by_name = dict()

        self.resource_page = ResourcePage(self, "resource")
        self.add_page(self.resource_page)

        self.finder = ResourceFinder()

        self.debug = False

    def init(self):
        for page in self.pages:
            page.init()

        for page in self.pages:
            page.seal()

    def add_page(self, page):
        assert not page.parent, "Page '%s' is not a root widget" % page.name
        assert page.name not in self.pages_by_name, \
            "A page called '%s' has already been added" % page.name

        self.pages.append(page)
        self.pages_by_name[page.name] = page

    def set_default_page(self, page):
        self.pages_by_name[""] = page

    def add_resource_dir(self, dir):
        self.finder.add_dir(dir)

    def get_resource(self, name):
        return self.finder.find(name)

    def __repr__(self):
        return self.__class__.__name__

class ResourcePage(Page):
    content_types_by_extension = {
        ".css": "text/css",
        ".gif": "image/gif",
        ".html": "text/html",
        ".jpeg": "image/jpeg",
        ".jpg": "image/jpeg",
        ".js": "text/javascript",
        ".png": "image/png",
        }

    def __init__(self, app, name):
        super(ResourcePage, self).__init__(app, name)

        self.rname = Parameter(app, "name")
        self.add_parameter(self.rname)

        self.then = datetime.utcnow()
        self.check_login = False

    def get_last_modified(self, session):
        return self.then

    def get_cache_control(self, session):
        return "max-age=86400"

    def get_content_type(self, session):
        name = self.rname.get(session)
        base, ext = os.path.splitext(name)
        ext = ext.lower()
        content_type = self.content_types_by_extension.get(ext, "text/plain")

        return content_type

    def do_render(self, session, *args):
        name = self.rname.get(session)

        if name:
            if name.startswith("/"):
                name = name[1:]

            resource = self.app.get_resource(name)

            if resource:
                return resource.read()
