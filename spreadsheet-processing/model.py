class Model(object):
    def __init__(self, site_url):
        self.site_url = site_url
        
        self.people = list()
        self.products = list()
        self.releases = list()
        self.source_modules = list()
        self.component_groups = list()
        self.components = list()
        self.features = list()
        self.channels = list()
        self.protocols = list()
        self.task_groups = list()
        self.tasks = list()
        
    def init(self):
        for person in self.people:
            person.init()

        for product in self.products:
            product.init()

        for release in self.releases:
            release.init()

        for source_module in self.source_modules:
            source_module.init()

        for group in self.component_groups:
            group.init()

        for component in self.components:
            component.init()

        for feature in self.features:
            feature.init()

        for channel in self.channels:
            channel.init()

        for protocol in self.protocols:
            protocol.init()

        for task_group in self.task_groups:
            task_group.init()

class ModelObject(object):
    def __init__(self, model, key, name):
        self.model = model
        self.key = key
        self.name = name

        self.url = None

        assert not hasattr(self.model, self.key), self.key

        setattr(self.model, self.key, self)

    def init(self):
        pass

    @property
    def link(self):
        if self.url is None:
            return self.name
            
        return "<a href=\"{}\">{}</a>".format(self.url, self.name)

    def __str__(self):
        return self.link

    def __repr__(self):
        return "{}({})".format(self.__class__.__name__, self.key)

class Person(ModelObject):
    def __init__(self, model, key, name):
        super(Person, self).__init__(model, key, name)

        self.login = self.key
        self.irc_nick = self.login
        self.role = None
        self.phone_number = None
        self.location = None

        self.email = "{}@redhat.com".format(self.login)

        self.hash = "#{}".format(self.name.lower())
        self.hash = self.hash.replace(" ", "-")

        self.tasks = list()
        
        self.model.people.append(self)

    def init(self):
        self.url = "https://mojo.redhat.com/people/{}".format(self.login)

class Product(ModelObject):
    def __init__(self, model, key, name):
        super(Product, self).__init__(model, key, name)

        self.upstream_url = None

        self.releases = set()
        self.source_modules = set()
        self.components = set()
        self.features = set()

        self.model.products.append(self)

    def init(self):
        if self.url is None:
            page = self.key.replace("_", "-")
            self.url = "{}/products/{}.html".format(self.model.site_url, page)
        
class Release(ModelObject):
    def __init__(self, model, product, key, name):
        super(Release, self).__init__(model, key, name)

        self.product = product

        self.prd_url = None
        self.erd_url = None
        self.erratum_url = None
        self.upstream_issues_url = None
        self.upstream_release_url = None  # XXX -> upstream_url
        self.downstream_issues_url = None
        self.downstream_release_url = None  # XXX -> downstream_url
        self.test_plan_url = None
        self.doc_plan_url = None

        self.model.releases.append(self)

class SourceModule(ModelObject):
    def __init__(self, model, key, name):
        super(SourceModule, self).__init__(model, key, name)

        self.upstream_url = None
        self.downstream_url = None

        self.components = set()
        self.releases = set()
        self.channels = dict() # Values are URLs for release artifacts
        
        self.model.source_modules.append(self)
        
class ComponentGroup(ModelObject):
    def __init__(self, model, key, name):
        super(ComponentGroup, self).__init__(model, key, name)

        self.components = set()
        self.features = set() # Computed from component features

        self.model.component_groups.append(self)

    def init(self):
        for component in self.components:
            for feature in component.features:
                self.features.add(feature)

class Component(ModelObject):
    def __init__(self, model, key, name, source_module):
        super(Component, self).__init__(model, key, name)

        self.source_module = source_module

        self.upstream_url = None
        self.upstream_issues_url = None

        self.downstream_url = None
        self.downstream_issues_url = None
        
        self.status = None
        
        self.developers = list()
        self.features = dict() # Values are feature status
        self.languages = list()
        self.platforms = list()
        self.protocols = list()
        self.tasks = list()

        self.model.components.append(self)

    def init(self):
        assert self.source_module is not None

        if self.url is None:
            self.url = self.upstream_url

        if self.url is None:
            self.url = self.downstream_url

class Feature(ModelObject):
    def __init__(self, model, key, name, tag=None):
        super(Feature, self).__init__(model, key, name)

        self.tag = tag

        self.model.features.append(self)

class Channel(ModelObject):
    def __init__(self, model, key, name):
        super(Channel, self).__init__(model, key, name)

        self.model.channels.append(self)

class Language(ModelObject):
    def __init__(self, model, key, name):
        super(Language, self).__init__(model, key, name)

class Platform(ModelObject):
    def __init__(self, model, key, name):
        super(Platform, self).__init__(model, key, name)
        
class Protocol(ModelObject):
    def __init__(self, model, key, name):
        super(Protocol, self).__init__(model, key, name)

class TaskGroup(ModelObject):
    def __init__(self, model, key, name):
        super(TaskGroup, self).__init__(model, key, name)

        self.tasks = list()
        
        self.model.task_groups.append(self)

class Task(object):
    def __init__(self, model, summary, group=None, person=None,
                 component=None, size=None, priority=None, jira_key=None):
        self.model = model
        self.group = group
        self.summary = summary
        self.person = person
        self.component = component
        self.size = size
        self.priority = priority
        self.jira_key = jira_key
        self.jira_link = "-"

        if self.jira_key is not None:
            self.jira_link = "<a href=\"https://issues.jboss.org/browse/{}\">{}</a>".format(self.jira_key, self.jira_key)

        self.model.tasks.append(self)

        if self.group is not None:
            self.group.tasks.append(self)

        if self.person is not None:
            self.person.tasks.append(self)

        if self.component is not None:
            self.component.tasks.append(self)
