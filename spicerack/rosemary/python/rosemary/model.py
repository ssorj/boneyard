from sqloperation import *
from sqlmodel import *
from sqlquery import *
from sqltype import *
import util
from cumin.util import xml_escape
from parsley.collectionsex import defaultdict

log = logging.getLogger("rosemary.model")

class RosemaryModel(object):
    def __init__(self):
        self._packages = list()
        self._packages_by_name = dict()

        self.sql_model = SqlModel(self)

        self.sql_logging_enabled = False

    def load_model_dir(self, paths):
        # Let this work across multiple directories
        if not type(paths) in (list, tuple):
            paths = [paths]

        for path in paths:
            assert os.path.isdir(path)
            extensions = os.path.join(path, "rosemary.xml")

            for name in os.listdir(path):
                file_path = os.path.join(path, name)

                if not os.path.isfile(file_path):
                    continue

                if file_path == extensions:
                    continue

                if file_path.endswith(".xml"):
                    self.load_model_file(file_path)

            if os.path.isfile(extensions):
                self.load_extensions(extensions)

    def load_model_file(self, path):
        tree = ElementTree()
        file = open(path, "r")

        try:
            tree.parse(file)
            self.load(tree.getroot())
        finally:
            file.close()

    def load_extensions(self, path):
        tree = ElementTree()
        file = open(path, "r")

        try:
            tree.parse(file)
            self.extend(tree.getroot())
        finally:
            file.close()

    def load(self, elem):
        # This is an attribute on a top level tag,
        # it should correspond to something like <schema package="blah">
        attr = elem.get("package")

        if attr:
            pkg_type = elem.get("package_type", None)
            pkg = RosemaryPackage(self, attr, pkg_type)
            pkg.load(elem)

        # This on the other hand is a tag itself.  It should
        # correspond to something like
        # <model>
        #    <package ....>
        #         stuff
        #    </package>
        for child in elem.findall("package"):
            pkg_type = child.get("package_type", None)
            pkg = RosemaryPackage(self, child.get("name"), pkg_type)
            pkg.load(child)

    def extend(self, elem):
        for child in elem.findall("package"):
            pkg = self._packages_by_name[child.get("name")]
            pkg.extend(child)

    def init(self):
        for pkg in self._packages:
            pkg.init()

        for pkg in self._packages:
            pkg.init_references()

    @classmethod
    def find_youngest(cls, rosemary_cls, cursor, **criteria):
        youngest = None
        if rosemary_cls._storage != "none":
            try:
                objects = rosemary_cls.get_selection(cursor, **criteria)
                if len(objects) > 0:
                    youngest = objects[0]
                    for obj in objects:
                        if obj.get_timestamp() > youngest.get_timestamp():
                            youngest = obj
            except:
                pass
        return youngest

    @classmethod
    def handle_persistent(cls, persistent):
        if persistent in ("y", "database"):
            return "database"
        elif persistent in ("n", "session"):
            return "session"
        elif persistent == "timestamp":
            return persistent
        return None
    
class RosemaryPackage(object):
    def __init__(self, model, name, pkg_type):
        self._model = model
        self._name = name
        self.pkg_type = pkg_type
        if self.pkg_type in (None, ""):
            self.pkg_type = "qmf"
        self.xml_class = self.get_xml_class()

        # Set in the extension xml file.  This specifies how
        # object data deletion is handled for classes in the
        # package.

        # There are 3 possibilities for 'persistent' in the xml:
        # "y" or "database" -- data is only deleted manually
        # "n" or "session"  -- data is deleted on startup (default)
        # "timestamp" -- data is deleted by the expire thread
        #   along with samples, governed by the same threshold

        # In all 3 cases, sample data is deleted by the expire thread
        # if it is enabled, governed by the threshold.  Persistent
        # only affects object data.

        # Note, "persistent" may also be set at the class
        # level in cases where packages contain classes with
        # different semantics.
        self.persistent = "session"

        self._model._packages.append(self)
        self._model._packages_by_name[self._name] = self

        mangled = self._name.replace(".", "_")

        if hasattr(self._model, mangled):
            raise Exception("Collision: %s" % mangled)

        setattr(self._model, mangled, self)

        self._classes = list()
        self._classes_by_name = dict()
        self._classes_by_lowercase_name = dict()

        self.sql_schema = SqlSchema(self._model.sql_model, self._name)

    def load(self, elem):
        groups_by_name = dict()

        for child in elem.findall("group"):
            name = child.get("name")
            groups_by_name[name] = child

        for child in elem.findall("class"):
            cls = self.xml_class(self, child.get("name"))
            cls.load(child, groups_by_name)

    def get_xml_class(self):
        # Split the pkg_type specifier on last .
        # Last item is the class type to use for this package.  
        # The convention is that type, capitalized and appended with "_class", 
        # names a class corresponding to the xml definition.
        # Previous items name a module under rosemary.
        try:
            mdl, cls = self.pkg_type.rsplit(".", 1)
        except ValueError:
            # no dot, just the class is given
            # default module to 'model'
            mdl = "model"
            cls = self.pkg_type        
        m = sys.modules["rosemary." + mdl.lower()]
        cls = m.__dict__.get(cls.capitalize() + "_class")
        return cls

    def extend(self, elem):
        persistent = elem.get("persistent")
        if persistent is not None:
            p = RosemaryModel.handle_persistent(persistent)
            if p is None:
                log.debug("Persistent value '%s' invalid for '%s',"\
                          "using default of '%s'" % \
                          (persistent, self._name, self.persistent))
            else:
                self.persistent = p

        for child in elem.findall("class"):
            cls = self._classes_by_name[child.get("name")]
            cls.extend(child)

    def init(self):
        for cls in self._classes:
            cls.init()

    def init_references(self):
        for cls in self._classes:
            cls.init_references()

    def __repr__(self):
        args = (self.__class__.__name__, self._name)
        return "%s(%s)" % args

class RosemaryClass(object):
    def __init__(self, package, name):
        self._package = package
        self._name = name

        # If _persistent is None, check_persistent will
        # return the value from self._package
        self._persistent = None

        self._package._classes.append(self)
        self._package._classes_by_name[self._name] = self
        self._package._classes_by_lowercase_name[self._name.lower()] = self

        assert not hasattr(self._package, self._name), self._name

        setattr(self._package, self._name, self)

        self._storage = "database"

        self._title = None
        self._object_title = None

        self._attributes = list()

        self._headers = list()
        self._headers_by_name = dict()

        self._references = list()
        self._references_by_name = dict()

        self._inbound_references = list()

        self._properties = list()
        self._properties_by_name = dict()

        self._statistics = list()
        self._statistics_by_name = dict()

        self._methods = list()
        self._methods_by_name = dict()

        self._indexes = list()
        self._indexes_by_name = dict()

        self.add_unique_to_samples = False

        # Ditionary of tuples, indicates which
        # columns are unique (either single columns
        # or groups of columns)
        self._unique_col_groups = defaultdict(list)

        # Similar for samples, indicate which indices
        # should be generated for the sample tables
        self._sample_index_col_groups = defaultdict(list)

        self._id = RosemaryAttribute(self, "_id")

        # Designates which field we will use as a timestamp
        # in Objects of this type.
        self.timestamp = ""

    def get_timestamp_col(self):
        return self.timestamp

    def load(self, elem, groups_by_name):
        log.debug("Loading %s", self)

        self._storage = elem.get("storage", "database")

        assert self._storage in ("database", "none")

        for child in elem.findall("group"):
            name = child.get("name")
            try:
                self.load_class_components(groups_by_name[name])
            except KeyError:
                log.error("Reference to group '%s' invalid", name)

                raise

        self.load_class_components(elem)

    def load_class_components(self, elem):
        for child in elem.findall("property"):
            name = child.get("name")
            if child.get("references"):
                attr = RosemaryReference(self, name)
            else:
                attr = RosemaryProperty(self, name)
            attr.load(child)

        for child in elem.findall("statistic"):
            stat = RosemaryStatistic(self, child.get("name"))
            stat.load(child)

#        for child in elem.findall("method"):
#            meth = RosemaryMethod(self, child.get("name"))
#            meth.load(child)

    def extend(self, elem):
        log.debug("Extending %s", self)

        self._title = elem.findtext("title")

        self._object_title = elem.findtext("object/title")

        persistent = elem.get("persistent")
        if persistent is not None:
            p = RosemaryModel.handle_persistent(persistent)
            if p is None:
                log.debug("Persistent value '%s' invalid for '%s',"\
                          "using default of '%s'" % \
                          (persistent, self._name, self._persistent))
            else:
                self._persistent = p

        for child in elem.findall("property"):
            prop = self._properties_by_name[child.get("name")]
            prop.extend(child)

            # If the attribute is flagged as the timestamp field,
            # then remember the name of the field so that it can
            # be set as the timestamp field when a new object is
            # created
            if prop.timestamp:
                self.timestamp = prop.name

        for child in elem.findall("statistic"):
            stat = self._statistics_by_name[child.get("name")]
            stat.extend(child)

            # If the attribute is flagged as the timestamp field,
            # then remember the name of the field so that it can
            # be set as the timestamp field when a new object is
            # created
            if stat.timestamp:
                self.timestamp = stat.name
            
#        for child in elem.findall("method"):
#            meth = self._methods_by_name[child.get("name")]
#            meth.extend(child)

        for child in elem.findall("index"):
            idx = RosemaryIndex(self, child.get("name"))
            idx.extend(child)

    def check_persistent(self):
        if self._persistent is None:
            return self._package.persistent
        return self._persistent

    def init(self):
        log.debug("Initializing %s", self)

        if not self._title:
            self._title = generate_title(self._name)

        self.add_sql_entities()

        self._id.sql_column = self.sql_table.key_column

        self.add_samples_sql()

        for hdr in self._headers:
            hdr.init()

        for prop in self._properties:
            # Properties will add themselves to
            # self._unique_col_groups.  
            # The unique constraints will
            # be generated in add_sql_contraints.
            prop.init()

        for stat in self._statistics:
            stat.init()

        for meth in self._methods:
            meth.init()

        for idx in self._indexes:
            idx.init()

        self.add_sql_constraints()
        self.add_sql_operations()
        self.add_sql_sample_operations()
        self.add_sql_sample_indices()

    def init_references(self):
        for ref in self._references:
            ref.init()

    def add_sql_entities(self):
        name = "%s_id_seq" % self._name
        self.sql_sequence = SqlSequence(self._package.sql_schema, name)

        self.sql_table = SqlTable(self._package.sql_schema, self._name)

        id_col = SqlColumn(self.sql_table, "_id", sql_int8)
        self.sql_table.key_column = id_col

        name = "%s_pk" % self._name
        SqlPrimaryKeyConstraint(self.sql_table, name, (id_col,))

    def add_sql_constraints(self):
        for k,v in self._unique_col_groups.iteritems():
            SqlUniqueConstraint(self.sql_table, k, v)

    def add_sql_operations(self):
        self.sql_get_new_id = SqlGetNewId(self.sql_table, self.sql_sequence)
        self.sql_select_by_id = SqlSelectObject(self.sql_table)
        self.sql_insert_object = SqlInsertObject(self.sql_table)
        self.sql_update_object = SqlUpdateObject(self.sql_table)
        self.sql_delete_object = SqlDeleteObject(self.sql_table)

        # If we've been marked as timestamp persistent, then
        # add an operation to delete objects by timestamp just
        # like samples
        if self.check_persistent() == "timestamp":
            try:
                timestamp = getattr(self.sql_table, self.timestamp)
                self.sql_timestamp_delete = SqlDeleteObjectSamples(
                    self.sql_table,
                    timestamp)
            except:
                pass

    def add_samples_sql(self):
        name = "%s_samples" % self._name
        table = SqlTable(self._package.sql_schema, name)
        self.sql_samples_table = table

    def add_sql_sample_indices(self):
        # Add indices based on the unique column groups
        # for the sample table
        for k,v in self._sample_index_col_groups.iteritems():
            SqlIndex(self._package.sql_schema, k, v)

    def add_sql_sample_operations(self):
        self.sql_samples_insert = SqlInsertObjectSamples(
            self.sql_samples_table)

        # Add delete by timestamp if the timestamp field is defined
        try:
            timestamp = getattr(self.sql_samples_table, self.timestamp)
            self.sql_samples_delete = SqlDeleteObjectSamples(
                self.sql_samples_table,
                timestamp)
        except:
            self.sql_samples_delete = None
            log.debug("Missing or invalid timestamp designation for class " \
                      "'%s', check xml" % self._name)
            
    def get_object(self, cursor, **criteria):
        sql = SqlSelect(self.sql_table)

        for name in criteria:
            # XXX need to translate ref=obj args here
            
            column = self.sql_table._columns_by_name[name]
            sql.add_filter(SqlValueFilter(column))

        sql.execute(cursor, criteria)

        record = cursor.fetchone()

        if not record:
            return

        obj = self._get_rosemary_object(None)

        self._set_object_attributes(obj, self.sql_table._columns, record)

        return obj

    def get_selection(self, cursor, **criteria):
        selection = list()
        sql = SqlSelect(self.sql_table)

        for name in criteria:
            # XXX need to translate ref=obj args here
            
            column = self.sql_table._columns_by_name[name]
            sql.add_filter(SqlValueFilter(column))

        sql.execute(cursor, criteria)
        
        for record in cursor.fetchall():
            obj = self._get_rosemary_object(None)

            self._set_object_attributes(obj, self.sql_table._columns, record)

            selection.append(obj)

        return selection
    
    def get_selection_samples(self, cursor, **criteria):
        selection = list()
        sql = SqlSelect(self.sql_samples_table)

        for name in criteria:
            # XXX need to translate ref=obj args here
            
            column = self.sql_table._columns_by_name[name]
            sql.add_filter(SqlValueFilter(column))

        sql.execute(cursor, criteria)
        
        for record in cursor.fetchall():
            obj = self._get_rosemary_object(None)

            self._set_object_attributes(obj, self.sql_samples_table._columns, record)

            selection.append(obj)

        return selection
    

    def get_selection_like(self, cursor, **criteria):
        selection = list()
        sql = SqlSelect(self.sql_table)

        for name in criteria:
            column = self.sql_table._columns_by_name[name]
            sql.add_filter(SqlLikeFilter(column))

        sql.execute(cursor, criteria)

        for record in cursor.fetchall():
            obj = self._get_rosemary_object(None)

            self.set_object_attributes(obj, self.sql_table._columns, record)

            selection.append(obj)

        return selection

    def get_object_by_id(self, cursor, id):
        assert id

        obj = self._get_rosemary_object(id)

        self.load_object_by_id(cursor, obj)

        return obj

    def get_new_id(self, cursor):
        self.sql_get_new_id.execute(cursor)

        values = cursor.fetchone()

        assert values

        return values[0]

    # Allow this to be overloaded so that
    # descendents of RosemaryClass can produce
    # descendents of RosemaryObject in create_object
    # and other places
    def _get_rosemary_object(self, id):
        return RosemaryObject(self, id)

    def create_object(self, cursor):
        id = self.get_new_id(cursor)
        return self._get_rosemary_object(id)

    def load_object_by_id(self, cursor, obj):
        assert isinstance(obj, RosemaryObject)
        assert obj._id, obj

        self.sql_select_by_id.execute(cursor, obj.__dict__)

        values = cursor.fetchone()

        if not values:
            raise RosemaryNotFound()

        self._set_object_attributes(obj, self.sql_table._columns, values)

    def _set_object_attributes(self, obj, columns, values):
        assert isinstance(obj, RosemaryObject)

        for column, value in zip(columns, values):
            setattr(obj, column.name, value)

        obj._load_time = datetime.now()

    def save_object(self, cursor, obj, columns=None):
        assert isinstance(obj, RosemaryObject)
        assert obj._id, obj

        if obj._load_time or obj._save_time:
            sql = self.sql_update_object
        else:
            sql = self.sql_insert_object

        if columns is None:
            columns = self.sql_table._columns

        sql.execute(cursor, obj.__dict__, columns=columns)

        obj._save_time = datetime.now()

    def add_object_sample(self, cursor, obj, columns=None):
        assert isinstance(obj, RosemaryObject)
        assert obj._id, obj

        if columns is None:
            columns = self.sql_table._columns

        self.sql_samples_insert.execute(cursor, obj.__dict__, columns=columns)
        
    def get_sample_filters_by_signature(self, sig, gen_cursor):
        # by default, there are no sample_filters, if you need them, 
        # please override this
        return []           

    def delete_object(self, cursor, obj):
        assert isinstance(obj, RosemaryObject)
        assert obj._id

        self.sql_delete_object.execute(cursor, obj.__dict__)

    def _delete_selection(self, cursor, table, **criteria):
        sql = SqlDelete(table)

        for name in criteria:
            column = table._columns_by_name[name]
            sql.add_filter(SqlValueFilter(column))

        sql.execute(cursor, criteria)
        return cursor.rowcount

    def delete_selection(self, cursor, **criteria):
        return self._delete_selection(cursor, self.sql_table, **criteria)

    def delete_sample_selection(self, cursor, **criteria):
        return self._delete_selection(cursor, 
                                      self.sql_samples_table, **criteria)

    def __repr__(self):
        args = (self.__class__.__name__, self._package._name, self._name)
        return "%s(%s,%s)" % args

class Qmf_class(RosemaryClass):
    def __init__(self, package, name):
        super(Qmf_class, self).__init__(package, name)

        name = "_qmf_agent_id"
        self._qmf_agent_id = RosemaryHeader(self, name, sql_text)
        self._qmf_agent_id.title = "Agent ID"

        name = "_qmf_object_id"
        self._qmf_object_id = RosemaryHeader(self, name, sql_text)
        self._qmf_object_id.title = "Object ID"

        name = "_qmf_create_time"
        self._qmf_create_time = RosemaryHeader(self, name, sql_timestamp)
        self._qmf_create_time.title = "Create Time"

        name = "_qmf_update_time"
        self._qmf_update_time = RosemaryHeader(self, name, sql_timestamp)
        self._qmf_update_time.title = "Update Time"

        name = "_qmf_delete_time"
        self._qmf_delete_time = RosemaryHeader(self, name, sql_timestamp)
        self._qmf_delete_time.title = "Delete Time"
        self._qmf_delete_time.optional = True

        # Default timestamp field for Qmf objects will be _qmf_update_time
        self.timestamp = "_qmf_update_time"

    def add_sql_operations(self):
        super(Qmf_class, self).add_sql_operations()
        self.sql_select_by_qmf_id = SqlSelectObjectByQmfId(self.sql_table)

    def add_sql_sample_operations(self):
        super(Qmf_class, self).add_sql_sample_operations()

        # Okay, our insert operation needs some extra columns
        # Add them here to the operation created by our parent.
        self.sql_samples_insert.extra_column_names = ("_qmf_agent_id",
                                                      "_qmf_object_id")

    def add_sql_constraints(self):
        # Add agent and object columns as a unique column set
        name = "%s_qmf_id_uq" % self._name
        self._unique_col_groups[name] = (self._qmf_agent_id.sql_column, 
                                         self._qmf_object_id.sql_column)
        super(Qmf_class, self).add_sql_constraints()

    def add_samples_sql(self):
        super(Qmf_class, self).add_samples_sql()
        a = SqlColumn(self.sql_samples_table, "_qmf_agent_id", sql_text)
        o = SqlColumn(self.sql_samples_table, "_qmf_object_id", sql_text)
        SqlColumn(self.sql_samples_table, "_qmf_update_time", sql_timestamp)

        name = "%s_qmf_id_idx" % self.sql_samples_table._name
        self._sample_index_col_groups[name] = (a, o)

    def get_object_by_qmf_id(self, cursor, agent_id, object_id):
        obj = self._get_rosemary_object(None)
        obj._qmf_agent_id = agent_id
        obj._qmf_object_id = object_id
        self.load_object_by_qmf_id(cursor, obj)
        return obj

    def load_object_by_qmf_id(self, cursor, obj):
        assert isinstance(obj, RosemaryQmfObject)
        assert obj._qmf_agent_id, obj
        assert obj._qmf_object_id, obj

        self.sql_select_by_qmf_id.execute(cursor, obj.__dict__)

        values = cursor.fetchone()

        if not values:
            raise RosemaryNotFound()

        self._set_object_attributes(obj, self.sql_table._columns, values)

    def get_signature(self, obj):
        # Return an ordered set of values that can uniquely
        # identify the object
        return [obj._qmf_agent_id.replace(":", "|"),
                obj._qmf_object_id]

    def get_object_by_signature(self, cursor, signature):
        # Use the signature to find the object
        agent_id, obj_id = signature
        # open-flash-chart can't handle the : in the agent id. Net even if
        # it's converted to %3A, so we have to change it
        agent_id = agent_id.replace("|", ":")
        return self.get_object_by_qmf_id(cursor, agent_id, obj_id)

    def get_sample_filters_by_signature(self, signature, gen_cursor):
        agent_id, obj_id = signature
        agent_id = agent_id.replace("|", ":")
        filters = []

        col = self.sql_samples_table._qmf_agent_id
        filters.append(SqlComparisonFilter(col, agent_id, 
                                           gen_cursor=gen_cursor))

        col = self.sql_samples_table._qmf_object_id
        filters.append(SqlComparisonFilter(col, obj_id,
                                           gen_cursor=gen_cursor))

        return filters

    # Allow this to be overloaded so that
    # descendents of RosemaryClass can produce
    # descendents of RosemaryObject in create_object
    # and other places
    def _get_rosemary_object(self, id):
        return RosemaryQmfObject(self, id)

class Generic_class(RosemaryClass):
    def __init__(self, package, name):
        super(Generic_class, self).__init__(package, name)

        # Columns marked unique will be added to the
        # sample table
        self.add_unique_to_samples = True
        self.source = ""
        self.database = ""
        self.collection = ""
        self.loading_class = ""

    def init(self):
        super(Generic_class, self).init()
        
        # Store a sorted list of the names of unique
        # column groups
        self.col_group_list = self._unique_col_groups.keys()
        self.col_group_list.sort()

        # Todo: this could be optimized if we use the shortest
        # set of unique column groups but probably there is only one
        if self._unique_col_groups is not None and len(self._unique_col_groups) > 0:
            self.signature_cols = self._unique_col_groups[self.col_group_list[0]]
        else:
            self.signature_cols = []

        # Set up a query that we can use on a unique
        # column set
        self.sql_select_signature = SqlSelect(self.sql_table)
        for c in self.signature_cols:
            self.sql_select_signature.add_filter(SqlValueFilter(c))

    def extend(self, elem):
        super(Generic_class, self).extend(elem)

        self.source = elem.findtext("source")
        self.database = elem.findtext("source/database")
        self.collection = elem.findtext("source/collection")
        self.loading_class = elem.findtext("loading_class/name")

    def load_class_components(self, elem):
        for child in elem.findall("property"):
            name = child.get("name")
            attr = RosemaryProperty(self, name)
            attr.load(child)

        for child in elem.findall("statistic"):
            stat = RosemaryStatistic(self, child.get("name"))
            stat.load(child)

    def get_signature(self, obj):
        # Return an ordered set of values that can uniquely
        # identify the object.
        # For plumage objects, this is going to be the list
        # of values in the columns marked unique.
        sig = []
        for c in self.signature_cols:
            # For each col, record the value from the object
            sig.append(getattr(obj, c.name))
        return sig

    def get_object_by_signature(self, cursor, signature):
        # signature is an ordered list of values corresponding
        # to self.signature_cols
        obj = self._get_rosemary_object(None)
        sig_idx = 0
        for c in self.signature_cols:
            setattr(obj, c.name, signature[sig_idx])
            sig_idx += 1
        self.load_object_by_signature(cursor, obj)
        return obj

    def load_object_by_signature(self, cursor, obj):
        assert isinstance(obj, RosemaryObject)

        self.sql_select_signature.execute(cursor, obj.__dict__)
        values = cursor.fetchone()
        if not values:
            raise RosemaryNotFound()
        self._set_object_attributes(obj, self.sql_table._columns, values)
        
class RosemaryAttribute(object):
    def __init__(self, cls, name):
        self.cls = cls
        self.name = name

        self.cls._attributes.append(self)

        assert not hasattr(self.cls, self.name), self.name

        setattr(self.cls, self.name, self)

        self.type = None
        self.references = None
        self.access = None
        self.unit = None
        self.index = None
        self.optional = None
        self.unique = None
        self.formatter = None
        self.storage = None

        self.title = None
        self.description = None
        self.short_title = None

        self.sql_column = None

    def process_unique(self, value):
        # If unique is None, "y" or "n" then it
        # is a boolean value and the column is not part
        # of a group, it is simply unique by itself
        if value is None:
            return False
        elif value in ("n", "y"):
            return value == "y"

        # Otherwise, the column is part of a multi-field
        # unique set where value is the name of the set
        return value

    def load(self, elem):
        self.type = elem.get("type")
        self.references = elem.get("references")
        self.access = elem.get("access")
        self.unit = elem.get("unit")
        self.index = elem.get("index", "n") == "y" and True
        self.optional = elem.get("optional", "n") == "y" and True
        self.unique = self.process_unique(elem.get("unique"))
        self.description = clean_description(elem.get("desc"))

    def extend(self, elem):
        self.title = elem.findtext("title")
        self.short_title = elem.findtext("short")
        formatter = elem.findtext("formatter")
        self.timestamp = elem.get("timestamp", "n") == "y"

        # Allow overloading of optional in the extensions
        # This is nice, because sometimes we have to mark
        # items as optional for backwards compatibility
        optional = elem.get("optional")
        if optional is not None:
            self.optional = optional == "y"

        # Same here
        unique = elem.get("unique")
        if unique is not None:                                              
            self.unique = self.process_unique(unique)

        if formatter:
            meth = getattr(util, formatter, None)

            if meth and callable(meth):
                self.formatter = meth

    def init(self):
        if not self.title:
            self.title = generate_title(self.name)

    def __repr__(self):
        args = (self.__class__.__name__, self.cls._name, self.name)
        return "%s(%s,%s)" % args

class RosemaryHeader(RosemaryAttribute):
    def __init__(self, cls, name, type):
        super(RosemaryHeader, self).__init__(cls, name)

        self.type = type

        self.cls._headers.append(self)
        self.cls._headers_by_name[self.name] = self

    def init(self):
        super(RosemaryHeader, self).init()

        assert not self.references

        self.sql_column = SqlColumn(self.cls.sql_table, self.name, self.type)
        self.sql_column.nullable = self.optional

class RosemaryReference(RosemaryAttribute):
    def __init__(self, cls, name):
        super(RosemaryReference, self).__init__(cls, name)

        self.cls._references.append(self)
        self.cls._references_by_name[self.name] = self

        self.that_cls = None

    def init(self):
        super(RosemaryReference, self).init()

        assert self.references

        tokens = self.references.split(":", 1)

        if len(tokens) == 2:
            pkg = self.cls._package._model._packages_by_name[tokens[0]]
            cls = tokens[1]
        else:
            pkg = self.cls._package
            cls = tokens[0]

        try:
            self.that_cls = pkg._classes_by_name[cls]
            self.that_cls._inbound_references.append(self)
        except KeyError:
            log.error("Reference to '%s' invalid", self.references)

            raise

        name = "_%s_id" % self.name
        self.name = name

        col = SqlColumn(self.cls.sql_table, name, sql_int8)
        col.foreign_key_column = self.that_cls.sql_table.key_column
        col.nullable = True

        self.sql_column = col

        name = "%s_fk" % col.name

        SqlForeignKeyConstraint(col.table, name, col, col.foreign_key_column)

class RosemaryProperty(RosemaryAttribute):
    def __init__(self, cls, name):
        super(RosemaryProperty, self).__init__(cls, name)

        self.cls._properties.append(self)
        self.cls._properties_by_name[self.name] = self

    def init(self):
        super(RosemaryProperty, self).init()

        assert not self.references

        type = sql_types_by_qmf_type_string[self.type]

        self.sql_column = SqlColumn(self.cls.sql_table, self.name, type)
        self.sql_column.nullable = self.optional

        # Save away refernces for generation of unique constraints and indices
        # If it's a single column marked unique, save it under its own name.
        if self.unique == True:
            name = "%s_%s_uq" % (self.cls.sql_table._name, self.name)
            self.cls._unique_col_groups[name] = (self.sql_column,)
        
        # If it's part of a group, append it to a group of columns named
        # for the group.
        elif self.unique:
            name = "%s_%s_uq" % (self.cls.sql_table._name, self.unique)
            self.cls._unique_col_groups[name].append(self.sql_column)

        # For some classes, add unique columns to the sample table, too.
        # Produce an index for the column(s) based on the 'unique' value.
        # These columns take the place of qmf_agent_id and qmf_object_id
        # for non-qmf records
        if self.cls.add_unique_to_samples and self.unique:
            col = SqlColumn(self.cls.sql_samples_table, self.name, type)
            col.nullable = self.optional
            if self.unique == True:
                name = "%s_%s_idx" % (self.cls.sql_samples_table._name, self.name)
                self.cls._sample_index_col_groups[name] = (col,)
            else:
                name = "%s_%s_idx" % (self.cls.sql_samples_table._name, self.unique)
                self.cls._sample_index_col_groups[name].append(col)

class RosemaryStatistic(RosemaryAttribute):
    def __init__(self, cls, name):
        super(RosemaryStatistic, self).__init__(cls, name)

        self.cls._statistics.append(self)
        self.cls._statistics_by_name[self.name] = self

    def init(self):
        super(RosemaryStatistic, self).init()

        assert not self.references

        type = sql_types_by_qmf_type_string[self.type]

        self.sql_column = SqlColumn(self.cls.sql_table, self.name, type)
        # always let stats be optional in the main table
        self.sql_column.nullable = True

        col = SqlColumn(self.cls.sql_samples_table, self.name, type)
        col.nullable = self.optional

class RosemaryMethod(object):
    def __init__(self, cls, name):
        self.cls = cls
        self.name = name

        self.cls._methods.append(self)
        self.cls._methods_by_name[self.name] = self

        self.description = None

        self.arguments = list()
        self.arguments_by_name = dict()

    def load(self, elem):
        self.description = clean_description(elem.get("desc"))

        for child in elem.findall("arg"):
            arg = RosemaryArgument(self, child.get("name"))
            arg.load(child)

    def extend(self, elem):


        pass

    def init(self):
        for arg in self.arguments:
            arg.init()

class RosemaryArgument(object):
    def __init__(self, meth, name):
        self.meth = meth

        self.name = name
        self.type = None
        self.direction = None
        self.description = None

        self.meth.arguments.append(self)
        self.meth.arguments_by_name[self.name] = self

    def load(self, elem):
        self.type = elem.get("type")
        self.direction = elem.get("dir")
        self.description = clean_description(elem.get("desc"))

    def extend(self, elem):
        pass

    def init(self):
        pass

class RosemaryIndex(object):
    def __init__(self, cls, name):
        self.cls = cls
        self.name = name

        self.cls._indexes.append(self)
        self.cls._indexes_by_name[self.name] = self

        self.attributes = list()

        self.sql_index = None

    def extend(self, elem):
        names = elem.get("attributes")

        for name in names.split():
            attr = getattr(self.cls, name)
            self.attributes.append(attr)

    def init(self):
        log.debug("Initializing %s", self)

        schema = self.cls._package.sql_schema
        name = "%s_%s_idx" % (self.cls._name, self.name)
        columns = [x.sql_column for x in self.attributes]

        self.sql_index = SqlIndex(schema, name, columns)

    def __repr__(self):
        args = (self.__class__.__name__, self.name)
        return "%s(%s)" % args

class RosemaryObject(object):
    def __init__(self, cls, id):
        for column in cls.sql_table._columns:
            setattr(self, column.name, None)

        self._class = cls
        self._id = id
        self._load_time = None
        self._save_time = None
        self._sample_time = None

        # This will be a generic alias that refers to a timestamp
        # field.  The actual field may be different for different classes,
        # but this name will work as an alias
        try:
            self._timestamp = getattr(self, cls.timestamp)
        except:
            self._timestamp = None

    # XXX prefix these with _
    def load(self, cursor):
        self._class.load_object_by_id(cursor, self)

    def save(self, cursor, columns=None):
        self._class.save_object(cursor, self, columns)

    def delete(self, cursor):
        self._class.delete_object(cursor, self)

    def add_sample(self, cursor, columns=None):
        self._class.add_object_sample(cursor, self, columns)

    def get_title(self):
        if self._class._object_title:
            return self._class._object_title % self.__dict__

        for attr in ("name", "Name"):
            if hasattr(self, attr):
                return self.get_formatted_value(attr, escape=True)

    def get_formatted_value(self, attr, escape=False):
        value = self.get_value(attr)
        if escape:
            value = xml_escape(value)
        formatter = None
        if attr in self._class._properties_by_name:
            formatter = self._class._properties_by_name[attr].formatter
        elif attr in self._class._statistics_by_name:
            formatter = self._class._statistics_by_name[attr].formatter
        #TODO: handle formatters headers as well
        return formatter and formatter(value) or value

    def get_value(self, attr):
        try:
            value = getattr(self, attr)
        except AttributeError:
            # there is no attr, return the value of the 1st property
            value = getattr(self, self._class._properties[0].name)

        return value

    def get_timestamp(self):
        return self._timestamp

    def get_signature(self):
        # return an ordered list of values that can uniquely
        # identify this object.  Let the class determine
        # the list.
        return self._class.get_signature(self)

    def __repr__(self):
        name = self.__class__.__name__
        args = (name, self._class, self._id, self._save_time)
        return "%s(%s,%i,%s)" % args

class RosemaryQmfObject(RosemaryObject):
    def fake_qmf_values(self):
        self._qmf_agent_id = "__rosemary__"
        self._qmf_object_id = str(datetime.now())
        self._qmf_create_time = datetime.now()
        self._qmf_update_time = datetime.now()

class RosemaryNotFound(Exception):
    pass

def generate_title(name):
    assert name

    chars = list()
    chars.append(name[0].upper())

    name = name[1:]

    prev = None
    curr = None
    next = None

    for i in range(len(name)):
        curr = name[i]

        try:
            next = name[i + 1]
        except IndexError:
            next = None

        if curr.isupper():
            if (prev and prev.islower()) or (next and next.islower()):
                chars.append(" ")
            if next and next.islower():
                curr = curr.lower()

        chars.append(curr)

        prev = curr

    return "".join(chars)

def clean_description(description):
    return description and " ".join(description.split()) or description
