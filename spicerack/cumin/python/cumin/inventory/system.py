from operator import itemgetter

from cumin.objectselector import ObjectSelector, ObjectLinkColumn, ObjectTable, ObjectTableColumn
from cumin.objectframe import ObjectFrame
from cumin.stat import StatSet, StatFlashChart
from cumin.formats import fmt_bytes, fmt_datetime
from cumin.model import CuminStatistic
from cumin.parameters import RosemaryObjectParameter
from cumin.sqladapter import ObjectSqlAdapter, ObjectSqlField
from cumin.util import *

from sage.wallaby.wallabyoperations import WallabyOperations, WBTypes

from wooly import Session, Widget
from wooly.datatable import *
from wooly.util import StringCatalog, xml_escape

strings = StringCatalog(__file__)

class ObjectSelectorTableNoCheckboxes(ObjectSelector):
    def __init__(self, app, name, cls):
        super(ObjectSelectorTableNoCheckboxes, self).__init__(app, name, cls)

    def create_table(self, app, name, cls):
        return ObjectTable(app, name, cls)

class SystemSelector(ObjectSelectorTableNoCheckboxes):
    def __init__(self, app, name):
        cls = app.model.com_redhat_sesame.Sysimage

        super(SystemSelector, self).__init__(app, name, cls)

        self.table.adapter = WallabyAndSqlAdapter(app, cls)

        frame = "main.inventory.system"
        col = ObjectLinkColumn(app, "name", cls.nodeName, cls._id, frame)
        self.add_column(col)
        self.add_search_filter(col)

        self.add_attribute_column(cls.osName)
        self.add_attribute_column(cls.machine)
        self.add_attribute_column(cls.memFree)
        
        col = self.LoadAverageColumn(app, "loadavg", cls.loadAverage1Min)
        self.add_column(col)
        
        col = SystemTagsColumn(app, "Tags", app.model.com_redhat_cumin_grid.Node.Tags, "Tags")
        self.add_column(col)
        col.cumin_module = "configuration"

        col = SystemCheckinColumn(app, "Checkin", app.model.com_redhat_cumin_grid.Node.Checkin, "Checkin")
        self.add_column(col)
        col.cumin_module = "configuration"

        self.enable_csv_export()
        
    class LoadAverageColumn(ObjectTableColumn): 
        def render_cell_content(self, session, data):
            content = data[self.table.adapter.fields_by_name['loadAverage1Min'].index]
            return content
        
        def render_header_content(self, session):
            return "Load average"
        
class SystemFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.com_redhat_sesame.Sysimage

        super(SystemFrame, self).__init__(app, name, cls)

        self.icon_href = "resource?name=system-36.png"

        overview = SystemStats(app, "overview", self.object)
        self.view.add_tab(overview)
        
        configuration = SystemTags(app, "configuration", self.object)
        self.view.add_tab(configuration)
        configuration.cumin_module = "configuration"
        
    def do_process(self, session):
        try:               
            id = self.id.get(session)
            obj = self.get_object(session, id)
            self.object.set(session, obj)
            super(ObjectFrame, self).do_process(session)
        except:
            # really nothing to do here since we don't have a traditional object to work with, which is ok
            pass
            
    def get_title(self, session):
        obj = self.object.get(session)
        if obj is not None:
            title = "%s '%s'" % (obj._class._title, obj.get_title())
        else:
            title = "System '%s'" % self.id.get(session)
        return title            

class SystemGeneralStatSet(StatSet):
    fmt_as_bytes = ("memFree", "swapFree")
    def __init__(self, app, name, object):
        super(SystemGeneralStatSet, self).__init__(app, name, object)

        self.attrs = ("memFree", "swapFree",
                       "loadAverage1Min", "loadAverage5Min",
                       "loadAverage10Min", "procTotal",
                       "procRunning")

    def render_item_value(self, session, item):
        stat, value = item
        if stat.name in self.fmt_as_bytes:
            return fmt_bytes(value*1024)
        return CuminStatistic.fmt_value(value, escape=True)

class SystemStats(Widget):
    def __init__(self, app, name, system):
        super(SystemStats, self).__init__(app, name)

        self.add_child(SystemGeneralStatSet(app, "stats", system))

        chart = self.MemoryFlashChart(app, "freemem", system)
        chart.chart_type = "percent"
        chart.stats = ("memFree",)
        self.add_child(chart)

        chart = StatFlashChart(app, "loadavg", system)
        chart.stats = ("loadAverage1Min",)
        self.add_child(chart)
    
        self.main_tmpl = WidgetTemplate(self, "html")

    def render_title(self, session):
        return "Overview"

    def render_slot_job_url(self, session):
        #job = Identifiable("XXX")
        #return self.page.main.grid.job.get_href(session, job, None)
        return session.marshal() # XXX
    
    def do_render(self, session, *args):
        if self.defer_enabled and not getattr(session, "background", None):
            writer = Writer()
            self.__defer_tmpl.render(writer, session, *args)
            return writer.to_string()
        else:
            writer = Writer()
            # if we have an object, we're in good shape
            # otherwise, show the "no content" template
            if self.frame.object.get(session):
                self.main_tmpl.render(writer, session, *args)
            else:
                self.nocontent_tmpl.render(writer, session, *args)
            return writer.to_string()    
        
    def render_error_msg(self, session, *args):
        return "There is no content to display for the chosen host.  This may be due to the sesame system being down."

    class MemoryFlashChart(StatFlashChart):
        def render_title(self, session, *args):
            return "Memory Usage"

        def get_href_params(self, session):
            params = super(SystemStats.MemoryFlashChart, self).get_href_params(session)
            params.append("tp=memTotal")

            return params

class SystemTagSet(Widget):
     def __init__(self, app, name, system):
        super(SystemTagSet, self).__init__(app, name)
        self.system = system
        self.main_tmpl = WidgetTemplate(self, "html")
        
     def render_title(self, session):
         return "Tags"        

     def _get_name(self, session):
         node_name = ""
         system = self.system.get(session)
         try:
             node_name = system.nodeName
         except:
             node_name = self.frame.id.get(session)
         return node_name

     def render_tags(self, session):
         node_name = self._get_name(session)
         try:
             tags = self.app.wallaby.get_tag_names(node_name)
         except AttributeError:
             tags = []
         tags_string = ", ".join(tags)         
                 
         return xml_escape(tags_string)

     def do_render(self, session, *args):
         if self.defer_enabled and not getattr(session, "background", None):
             writer = Writer()
             self.__defer_tmpl.render(writer, session, *args)
             return writer.to_string()
         else:
             writer = Writer()
             # if we have an object, we're in good shape
             # otherwise, show the "no content" template
             node_name = self._get_name(session)
             if self.frame.object.get(session) or \
                type(node_name) in (str,unicode) and node_name != "":
                 self.main_tmpl.render(writer, session, *args)
             else:
                 self.nocontent_tmpl.render(writer, session, *args)    
             return writer.to_string()    

     def render_error_msg(self, session, *args):
        return "Host data may have changed.  Return to the Inventory page and try again"

class SystemTags(Widget):
     def __init__(self, app, name, system):
        super(SystemTags, self).__init__(app, name)
        
        self.tag_set = SystemTagSet(app, name, system)
        self.add_child(self.tag_set)        
        
     def render_title(self, session):
         return "Configuration"

class WallabyAndSqlAdapter(ObjectSqlAdapter):
    
    def get_count(self, values):
        options = DataAdapterOptions()
        options.limit = 10000
        options.offset = 0
        return len(self.get_data(values, options))
        
    def get_data(self, values, options):
        #first, fetch all the sql data, unsorted since we will sort and limit it after merging the wallaby data
        requested_sort_field = options.sort_field
        requested_limit = options.limit
        requested_offset = options.offset
        options.sort_field = None
        options.limit = 10000
        options.offset = 0
        sqldata = super(WallabyAndSqlAdapter, self).get_data(values, options)
        
        #now get the wallaby data
        wallaby_nodes = self.app.wallaby.get_data(WBTypes.NODES, values)
        
        data = list()
        if len(sqldata) > 0 and len(wallaby_nodes) > 0:  #means that we have both sesame and wallaby data
            #now merge them
            for i, node in enumerate(wallaby_nodes):
                match_index = [i for i, y in enumerate(sqldata) if y[1] == node.name]
                if len(match_index) > 0:
                    ## merge-in the wallaby data to the matched node entry in sqldata
                    new_record = list(sqldata[match_index[0]])
                    new_record.append(", ".join(self.app.wallaby.get_tag_names(node)))
                    new_record.append(node.last_checkin)
                    sqldata[match_index[0]] = tuple(new_record)
                else:
                    # there was no match found, add a wallaby-only row
                    data_row = tuple([node.name, node.name, "", "", "", "", ", ".join(self.app.wallaby.get_tag_names(node)), node.last_checkin])
                    sqldata.append(data_row)
            data = sqldata
        elif len(sqldata) > 0:  # we only have sesame data
            for node in sqldata:
                node_data = list(node)
                data_row = tuple([node_data[0], node_data[1], node_data[2], node_data[3], node_data[4], node_data[5], [], ""])
                data.append(data_row)
        else:  # we have only wallaby data
            for node in wallaby_nodes:
                # using the node name for the [0] element in this case will allow 
                #other pages to use the id as the node lookup key against the wallaby data
                data_row = tuple([node.name, node.name, "", "", "", "", ", ".join(self.app.wallaby.get_tag_names(node)), node.last_checkin])
                data.append(data_row)
                
        options.sort_field = requested_sort_field
        options.limit = requested_limit
        options.offset = requested_offset          
        data = self.sort_rows(data, options)
        data = self.limit_rows(data, options)

        return data
    
    def limit_rows(self, rows, options):
        # return only the current page
        first_index = options.offset
        last_index = len(rows)
        if options.limit:
            last_index = options.offset + options.limit

        page = rows[first_index:last_index]

        return page    
    
    def sort_rows(self, rows, options):
        if len(rows) > 10000 or options.sort_field is None:
            return rows

        sort_field = options.sort_field
        rev = options.sort_ascending == False
        try:
            return sorted(rows, key=lambda k: k[sort_field.index].lower(), reverse=rev)    
        except AttributeError:
            #since long and float fields will not have lower()
            return sorted(rows, key=itemgetter(sort_field.index), reverse=rev)
    

class DerivedTableColumn(ObjectTableColumn):
    def __init__(self, app, name):
        super(DerivedTableColumn, self).__init__(app, name, None)

    def init(self):
        # avoid ObjectTableColumn's init() since we are setting up our own field
        super(ObjectTableColumn, self).init()

        self.field = self.get_field()

    def get_field(self):
        raise "Not Implemented"    
   
class TagsField(DataAdapterField):
    def __init__(self, adapter, column):
        super(TagsField, self).__init__(adapter, column, str)
        
    def get_content(self, session, record):
        value = ""
        try:
            value = record[self.index]        
            value = truncate_text(value, 30, True)
        except Exception, e:
            pass
        return value
    
    def get_title(self, session):
        return "Tags"  
    
       
class SystemTagsColumn(DerivedTableColumn):
    def __init__(self, app, name, attr, title):
        super(SystemTagsColumn, self).__init__(app, name)

        self.attr = attr
        self.title = title
        self.format_method = getattr(attr, "unit", None)

    def get_field(self):
        field = TagsField(self.table.adapter, self.name)
        return field   
    
    def render_cell_title(self, session, record):
        value = ""
        try:
            value = record[self.field.index]
        except Exception:
            pass #no data to show is a reasonable case if a node has wallaby, but doesn't really use it 
        return value

    def render_text_align(self, session):
        return "right"

class CheckinField(DataAdapterField):
    def __init__(self, adapter, column):
        super(CheckinField, self).__init__(adapter, column, str)
               
    def get_content(self, session, record):
        value = ""
        try:
            value = record[self.index]   
            if value > 0:
                checkin_value = datetime.fromtimestamp(float(value/1000000))  # the timestamps we get are too large
                value = fmt_datetime(checkin_value, sec=True)
            else:
                value = "Never"     
        except Exception, e:
            pass
        return value    
    
    def get_title(self, session):
        return "Last checkin"  

class SystemCheckinColumn(DerivedTableColumn):
    def __init__(self, app, name, attr, title):
        super(SystemCheckinColumn, self).__init__(app, name)

        self.attr = attr
        self.title = title
        self.format_method = getattr(attr, "unit", None)
        self.cumin_module = "configuration"

    def get_field(self):
        field = CheckinField(self.table.adapter, self.name)
        return field  
    
    def render_text_align(self, session):
        return "right"  

