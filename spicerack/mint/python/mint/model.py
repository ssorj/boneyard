from rosemary.model import *

from util import *

log = logging.getLogger("mint.model")

class MintModel(RosemaryModel):
    def __init__(self, app, model_dir):
        super(MintModel, self).__init__()

        self.app = app
        self.model_dir = model_dir

        self.agents_by_id = dict()

        # int seq => callable
        self.outstanding_method_calls = dict()

        self.lock = Lock()

    def check(self):
        log.info("Checking %s", self)
        
        if not type(self.model_dir) in (tuple, list):
            self.model_dir = [self.model_dir]

        for dirs in self.model_dir:
            assert os.path.isdir(dirs)
            log.debug("Model dir exists at '%s'", dirs)

    def init(self):
        log.info("Initializing %s", self)

        self.load_model_dir(self.model_dir)

        super(MintModel, self).init()

    def print_event(self, level, message, *args):
        log.debug(message, *args)

        if self.app.print_event_level >= level:
            print datetime.now(), message % args

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.model_dir)

class MintAgent(object):
    def __init__(self, model, id):
        self.model = model
        self.id = id

        self.last_heartbeat = None

        self.objects_by_id = dict()
        self.deferred_links_by_id = defaultdict(list)

        assert self.id not in self.model.agents_by_id
        self.model.agents_by_id[self.id] = self

    def delete(self):
        assert self.model

        del self.model.agents_by_id[self.id]

        self.model = None

    def get_object(self, cursor, cls, object_id):
        try:
            obj = self.objects_by_id[object_id]
        except KeyError:
            obj = cls.get_object_by_qmf_id(cursor, self.id, object_id)
            self.objects_by_id[object_id] = obj

        return obj

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, self.id)
