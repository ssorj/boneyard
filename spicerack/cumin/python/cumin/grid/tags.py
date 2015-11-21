import logging

from operator import itemgetter

from wooly import Widget, Attribute
from wooly.util import StringCatalog, Writer, escape_amp, escape_entity, unescape_entity
from wooly.datatable import DataAdapterOptions, DataAdapterField, DataTableColumn, DataTable, DataAdapter
from wooly.widgets import RadioModeSet, WidgetSet
from wooly.template import WidgetTemplate
from wooly.forms import *
from wooly.table import Table, TableColumn
from wooly.tables import *

from cumin.formats import fmt_link, fmt_datetime
from cumin.objectselector import *
from cumin.objectframe import *
from cumin.parameters import RosemaryObjectParameter
from cumin.task import TaskLink, Task, ObjectTaskForm
from cumin.widgets import *
from cumin.stat import *
from cumin.util import xml_escape

from sage.wallaby.wallabyoperations import WallabyOperations, WBTypes
from sage.util import *

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.tags")

class ResponseAdapter(ObjectQmfAdapter):
    '''
    This class is necessary to act as an adapter to take the response
    that we get from wallaby and turn it into something that we can readily
    display in a table format.  Typically, a table will have an adapter assigned
    to do the transformations necessary for display.
    '''
    def get_count(self, values):
        ''' Returns the current count of rows for the table (after filtering which is done in get_data() '''
        data = self.get_data(values, None)
        return len(data)

    def get_data(self, values, options):
        ''' 
        Calls do_get_data to fetch the remote data, then calls filter,
        sort and limit to sift through the data.        
        '''        
        data = self.do_get_data(values)        
        rows = self.process_results(data)
        
        rows = self.filter_rows(rows, values)
        if options:            
            rows = self.sort_rows(rows, options)
            rows = self.limit_rows(rows, options)

        return rows

    def process_results(self, results):
        ''' take the dict response from the call and return a list of lists '''
        records = list()

        if results:
            for i, result in enumerate(results):
                row = self.process_record(i, results[i])
                records.append(row)

        return records    
    
    def filter_rows(self, rows, values):
        '''
        Looks for the field name and filter value in the 'values' parameter, does a "contains" filtering on 
        each rows entry for the given field.
        ''' 
        filtered = list()
        filter_field = values.keys()[0]
        filter_text = values[filter_field].replace("%","")
        
        for row in rows:
           if filter_text.lower() in row[self.fields_by_name[filter_field].index].lower():
                filtered.append(row)
        return filtered   
    
    def sort_rows(self, rows, options):
        if len(rows) > self.max_sortable_records:
            return rows

        sort_field = options.sort_field
        rev = options.sort_ascending == False

        try:
            return sorted(rows, key=lambda k: k[sort_field.index].lower(), reverse=rev)    
        except AttributeError:
            #since long and float fields will not have lower()
            return sorted(rows, key=itemgetter(sort_field.index), reverse=rev)
        
    
class TagsAdapter(ResponseAdapter):
    '''
    This class is meant to adapt the wallaby response for get_data(TAGS) into a format appropriate
    for displaying in the tags table
    '''
    def do_get_data(self, values):
        data = []
        try:
            wallaby_tags = self.app.wallaby.get_data(WBTypes.TAGS)
            wallaby_features = self.app.wallaby.get_data(WBTypes.FEATURES)
            
            for i, tag in enumerate(wallaby_tags):
                data.append({'Tag':str(escape_entity(tag.name)), 
                             'Features':", ".join(tag.features), 
                             'NumHosts':len(self.app.wallaby.get_node_names(tag)), 
                             'Host':self.app.wallaby.get_node_names(tag)} )
                
        except:
            log.debug("Problem adapting wallaby response", exc_info=True)
        
        return data    
    
    def process_results(self, results):
        """ Take the get_data response and process it for viewing by tags """

        records = list()
        if results:
            for result in results:
                #Tag goes in the 0 and 1 column, 0 for checkbox value, 1 for the column value
                records.append([result['Tag'], 
                                result['Tag'], 
                                result['Features'], 
                                result['NumHosts'], result['Host']])

        return records
    
    
class NodesAdapter(ResponseAdapter):
    '''
    This class is meant to adapt the wallaby response for get_data(NODES) into a format appropriate
    for displaying in the nodes table
    '''
    def process_record(self, key, record):
        """ Take the get_data response and process it for viewing by nodes """
        return [record["Host"],record["Tags"],record["Checkin"]]    

    def do_get_data(self, values):
        '''
        Make the wallaby call and return a list of dicts that will be 
        formatted for the table by the process_record method
        '''
        wallaby_nodes = self.app.wallaby.get_data(WBTypes.NODES)
        data = []
        for i, node in enumerate(wallaby_nodes):
            data.append({'Host':node.name, 
                         'Tags':self.app.wallaby.get_tag_names(node), 
                         'Checkin':node.last_checkin})
        
        return data

class ObjectSelectorNoCheckboxes(ObjectSelector):
    '''
    All of the ObjectSelector goodness, but without the checkboxes that come from the default ObjectSelectorTable
    '''
    def __init__(self, app, name, cls):
        super(ObjectSelectorNoCheckboxes, self).__init__(app, name, cls)

    def create_table(self, app, name, cls):
        ''' override the default to give us a plain ObjectTable rather than and ObjectSelectorTable '''
        return ObjectTable(app, name, cls)   

class TagObjectView(ObjectView):
    ''' necessary so that we can override the render_title method
        to get the name from our tag object
    '''
    def render_title(self, session):
        obj = self.object.get(session)
        if obj is not None:
            return xml_escape(obj.name)
        else:
            return ""
    
    def add_details_tab(self):
        pass    

class TagObjectFrame(Frame, ModeSet):    
    '''
    This frame houses the view page for a tag, which is a non-traditional object
    in the sense that it does not live in the cumin database.  Given that, we 
    need to make a few changes to the typical functionality.
    '''
    def __init__(self, app, name, cls):
        super(TagObjectFrame, self).__init__(app, name)

        self.cls = cls

        # This will hold the id of the object that should be assigned 
        # to self.object (it is the _id field from a sql table).
        # Both the id and the object are typically determined during
        # the "process" pass before a page is rendered.
        self.id = StringParameter(app, "id")
        self.add_parameter(self.id)

        # This will be given a value during the "process" pass after
        # self.id is determined (lookup by id)
        self.object = Attribute(app, "object")
        self.add_attribute(self.object)       
        self.view = TagObjectView(app, "view", self.object)
        self.add_child(self.view)
        self.icon_href = "resource?name=action-36.png"
        self.tasks = list()

    def init(self):
        super(TagObjectFrame, self).init()
        assert self.cls, self
        for task in self.tasks:
            task.init()

    def get_href(self, session, id):
        branch = session.branch()
        self.id.set(branch, id)
        self.view.show(branch)
        return branch.marshal()

    def do_process(self, session):
        id = self.id.get(session)
        assert id
        obj = self.get_object(session, id)
        self.object.set(session, obj)
        super(TagObjectFrame, self).do_process(session)

    def get_object(self, session, id):
        return self.app.wallaby.get_tag_by_name(id)
        
class TagOverview(Widget):
    '''
    This is the contents of the "overview" tab that should be in the tag frame
    '''
    def __init__(self, app, name, tag):
        super(TagOverview, self).__init__(app, name)

        self.add_child(TagGeneral(app, "taggen", tag))
        
    def render_title(self, session):
        return "Overview"
    
class TagGeneral(Widget):
    '''
    This will display the general details for a tag (namely, the hosts
    and features)
    '''
    def __init__(self, app, name, tag):
        super(TagGeneral, self).__init__(app, name)
        self.update_enabled = True
        self.tag = tag
 
    def render_hosts(self, session):
        retval = ""
        try:
            obj = self.tag.get(session)
            retval = xml_escape(", ".join(self.app.wallaby.get_node_names(obj)))
        except Exception, e:
            log.debug("Exception in rendering tag hosts, tags probably not loaded yet: %s", e.message)
        return retval
    
    def render_features(self, session):
        retval = ""
        try:
            obj = self.tag.get(session)
            retval = xml_escape(", ".join(obj.features))
        except Exception, e:
            log.debug("Exception in rendering tag features, tags probably not loaded yet: %s", e.message)
        return retval
    
    def render_hosts_title(self, session):
        return "Hosts"

    def render_features_title(self, session):
        return "Features"   
        
class TagsFrame(TagObjectFrame):
    def __init__(self, app, name):
        cls = app.model.com_redhat_cumin_grid.Node
        super(TagsFrame, self).__init__(app, name, cls)
        
        self.set_tags = TagsNodeEditTask(app, self)
        self.set_nodes = TagsTagEditTask(app, self)
        self.set_features = TagsFeatureEditTask(app, self)
        
        self.overview = TagOverview(app, "tagoverview", self.object)
        self.view.add_tab(self.overview)

    def get_title(self, session):
        retval = ""
        try:
            retval = "Tag '%s'" % xml_escape(self.object.get(session).name)
        except Exception, e:
            pass
        return retval
        
class TagInventory(ObjectSelector):
    '''
    Table that will display the list of all tags across the system.
    '''
    def __init__(self, app, name):
        cls = app.model.com_redhat_cumin_grid.Node
        super(TagInventory, self).__init__(app, name, cls)
        self.table.adapter = TagsAdapter(app, cls)
        
        tag_add_task = AddTags(app)
        link = TaskLink(app, "tag_add", tag_add_task)
        self.links.add_child(link)
        
        self.activate_config_task = ActivateConfigTask(app)
        link = TaskLink(app, "actlink", self.activate_config_task)
        self.links.add_child(link)   
        
        col = self.TagColumn(app, "tagcol", cls.Tags, cls.Tags, "main.grid.tag")  
        col.width = "20%"  
        self.add_column(col)  
        self.add_search_filter(col)
        
        col = self.FeatureColumn(app, "featcol", cls.Features)
        col.width = "60%"    
        self.add_column(col)  
        
        col = self.HostCountColumn(app, "hostcount", cls.NumHosts)
        col.width = "20%"    
        self.add_column(col)  

        RemoveNodeTags(app, self, "removetags")
        
        self.enable_csv_export()
        
    def render_title(self, session):
        return "Configuration"
    
    class TagColumn(ObjectLinkColumn):      
        def render_cell_href(self, session, record):
            id = unescape_entity(record[self.id_field.index])
            frame = self.page.page_widgets_by_path[self.frame_path]
    
            if isinstance(frame, TagObjectFrame):
                return frame.get_href(session, id)
            else:
                return id #not able to get a link

    class FeatureColumn(ObjectTableColumn): 
        '''
        This column will display the features that are currently assigned to a tag.
        If a tag has no features on it, <add features to this tag> will be displayed instead.
        '''     
        def render_cell_content(self, session, data):
            feature_list = data[2]
            features = truncate_text(feature_list, 70, True)
            return features
        
        def render_cell_title(self, session, data):
            return data[2]
        
    class HostCountColumn(ObjectTableColumn): 
        def render_cell_content(self, session, data):
            tags = super(TagInventory.HostCountColumn, self).render_cell_content(session, data)
            return tags
        
        def render_header_content(self, session):
            return "Hosts"
        
        def render_text_align(self, session):
            return "right"
            

class NodeInventory(ObjectSelectorNoCheckboxes):
    '''
    Table that will display the list of nodes, their (possibly abbreviated) list of tags and
    the last checkin time for that node.
    '''
    def __init__(self, app, name):
        cls = app.model.com_redhat_cumin_grid.Node
        super(NodeInventory, self).__init__(app, name, cls)
        self.table.adapter = NodesAdapter(app, cls)

        col = self.NodeColumn(app, "nodecol", cls.Host)                       
        self.add_column(col)
        self.add_search_filter(col)
        
        col = self.TagsColumn(app, "tagcol", cls.Tags)
        self.add_column(col)
        
        col = self.CheckinColumn(app, "checkcol", cls.Checkin)
        self.add_column(col)        
        
        self.update_enabled = False
        
    def get_data_values(self, session):
        values = super(NodeInventory, self).get_data_values(session)
        values['session'] = session
        return values
        
    def render_title(self, session):
        return "Nodes"
    
    class CheckinColumn(ObjectTableColumn):
        def render_cell_content(self, session, data):
            checkin_timestamp = super(NodeInventory.CheckinColumn, self).render_cell_content(session, data)
            if checkin_timestamp > 0:
                checkin_value = datetime.fromtimestamp(float(checkin_timestamp/1000000))  # the timestamps we get are too large
                retval = fmt_datetime(checkin_value, sec=True)
            else:
                retval = "Never"     
            return retval
        
        def render_header_content(self, session):
            return "Last checkin"
        
        def render_text_align(self, session):
            return "right"
    
    class TagsColumn(ObjectTableColumn):
        def render_cell_content(self, session, data):
            tags_list = super(NodeInventory.TagsColumn, self).render_cell_content(session, data)
            tags = ""
            if tags_list:
                for tag in tags_list:
                    tags = tags + "," + str(tag)
                tags = tags[1:]
            retval = truncate_text(tags, 50, True)
            return retval
    
    class NodeColumn(ObjectTableColumn):      
        def render_cell_content(self, session, data):
            node_name = super(NodeInventory.NodeColumn, self).render_cell_content(session, data)
            tags_list = data[1]
            tags = ""
            if tags_list:
                for tag in tags_list:
                    tags = tags + "," + str(tag)
                tags = tags[1:]
            self.frame.tag.set_tags.form.node_name.set(session, node_name)
            self.frame.tag.set_tags.form.tags.set(session, tags)           
            href = self.frame.tag.set_tags.get_href(session)
            return fmt_link(href, node_name)
        
class ActivateConfigurationForm(ObjectTaskForm):
    '''
    This form is used to display a button that will trigger activation of the current wallaby configuration.
    '''
    def __init__(self, app, name, task, cls):
        super(ActivateConfigurationForm, self).__init__(app, name, task, cls)
        
        self.label = self.LabelField(app, "labelf")
        self.add_field(self.label)
               
    def render_submit_content(self, session):
        ''' overriding base method to control the label on the submit button '''
        return "Activate"

    def process_submit(self, session):
        if not self.validate(session):
            log.debug("Wallaby configuration activation errors")
            #  do something to capture error
        if not self.errors.get(session):
            # do the actual activation                    
            self.task.invoke(session, None)            
            #look at result of invoke....if good, proceed, otherwise might need to ramain on form
            url = self.return_url.get(session)
            self.page.redirect.set(session, url)        
    
    def validate(self, session):
        results = self.app.wallaby.validate_configuration()
        
        #handle the set of explanations that could come back if things didn't go well
        try:
            if len(results[0]) > 0:
                error_string = ""
                for error_host in results[0].keys():
                    for error_type in results[0][error_host].keys():
                        for error in results[0][error_host][error_type]:
                            error_string = error_string + "%s: %s: %s" % (error_host, error_type, error)
                self.errors.add(session, FormError(error_string))
                log.info("Results from validate_configuration: %s" % error_string)
    
            # handle the set of warnings that come back if things didn't go well            
            if len(results[1]) > 0:
                for error in results[1]:
                    self.errors.add(session, FormError(error))
                    log.info("Results from validate_configuration: %s" % error)            
                return False
            else:
                return True
        except Exception, e:
            error_msg = "Errors encountered parsing results of configuration activation"
            log.error(error_msg)
            self.errors.add(session, FormError(error_msg))
            return False
             
        
    def render_title(self, session):
        ''' appears in the top "bar" of the form display '''
        return "Activate pool configuration"
    
    def render_form_class(self, session):
        return " ".join((super(ActivateConfigurationForm, self).render_form_class(session), "mform"))
        
    class LabelField(Label):
        ''' this is just text that appears in place of actual form fields '''
        def __init__(self, app, name):
            super(ActivateConfigurationForm.LabelField, self).__init__(app, name)
            self.text = "Activate your current wallaby configuration? \
                         This will activate all changes (including those made outside of cumin) \
                         since your last activation."
            
class CreateTags(ObjectTaskForm):
    '''
    This form is used to display a single input field that will handle a comma separated 
    list of tags to be created.
    '''
    def __init__(self, app, name, task, cls):
        super(CreateTags, self).__init__(app, name, task, cls)
        
        self.tag = self.TagNamesField(app, "tag")
        self.add_field(self.tag)

    def process_submit(self, session):
        tag = self.tag.get(session)
        self.tag.validate(session)
        if not self.errors.get(session):
            self.tag.set(session, tag)
        
            self.task.invoke(session, None, tag)            
      
        url = self.return_url.get(session)
        self.page.redirect.set(session, url)        
        
    def render_tags_id(self, session):
        return self.tag.input.path
          
    def render_title(self, session):
        return "Create a tag"      
    
    class TagNamesField(StringField):
        def __init__(self, app, name):
            super(CreateTags.TagNamesField, self).__init__(app, name)
            self.help = "*Comma separated list"
            
        def render_title(self, session):
            return("Tag names ")
        
    def render_form_class(self, session):
        return " ".join((super(CreateTags, self).render_form_class(session), "mform"))        
        
class RemoveTags(ObjectSelectorTaskForm):
    '''
    This form is used to allow the user to pick a set of tags to be removed.
    We use ObjectSelectorTakForm because it acts on selections from the ObjectSelector it
    originates from.
    '''
    def __init__(self, app, name, task, cls):
        super(RemoveTags, self).__init__(app, name, task)
        
        self.task = task
        
    def get_selection(self, session):
        ''' return the set of checkboxes from the ObjectSelector that were set in self.ids '''
        ids = self.ids.get(session)
        selection = [escape_entity(id) for id in ids]
        
        self.selection.set(session, selection)
        return len(selection)        

    def process_submit(self, session):
        tags_to_kill = self.selection.get(session)
        
        if not self.errors.get(session):
            self.task.invoke(session, tags_to_kill)
      
        url = self.return_url.get(session)
        self.page.redirect.set(session, url)
        
    def render_tags_id(self, session):
        return self.tag.input.path
          
    def render_title(self, session):
        return "Delete tags"      
    
    def render_form_class(self, session):
        return " ".join((super(RemoveTags, self).render_form_class(session), "mform"))       
       
class EditNodeTagsForm(ObjectFrameTaskForm):
    '''
    This form is designed to allow the editing of tags for any single node
    '''
    def __init__(self, app, name, task):
        super(EditNodeTagsForm, self).__init__(app, name, task)

        self.node_name = self.NodeName(app, "node_name")
        self.add_field(self.node_name)

        self.tags = self.Tags(app, "tags")
        self.add_field(self.tags)
        
        self.new_tags = self.TagsList(app, "ptag")
        self.add_field(self.new_tags)
        
        self.update_enabled = False
        
                       
    def process_submit(self, session):
        orig_tags_value = self.tags.input.get(session)
        new_tags_value = self.new_tags.get(session)
        
        self.tags.validate(session)
        if not self.errors.get(session):
            self.tags.set(session, new_tags_value)
        
            node_name = self.node_name.get(session)
            negotiator = self.object.get(session)

            self.task.invoke(session, negotiator, node_name, new_tags_value)
            self.task.exit_with_redirect(session)

    def render_form_class(self, session):
        return " ".join((super(EditNodeTagsForm, self).render_form_class(session), "mform"))
    
    class TagsList(PageableFilteredSelect):
        '''
        This class takes care of displaying the tags for the given node in a filterable select box 
        that is pageable. 
        '''
        def __init__(self, app, name):
            super(EditNodeTagsForm.TagsList, self).__init__(app, name)
        
        def render_items(self, session):    
            items = self.do_get_items(session)     
            tags_string = ""
            
            given_node = self.form.node_name.input.param.get(session)
            selected_tags = self.app.wallaby.get_tag_names(given_node)
            
            for i, tag in enumerate(items):
                selected = ""
                if(selected_tags and tag.title in selected_tags):
                    selected = " selected='selected' "
                tags_string = tags_string + "<option id='" + str(i) + "'" + selected + ">" + tag.title + "</option>\n"
            
            return tags_string
        
        def do_get_items(self, session):
            tags = fetchItems(self, session, WBTypes.TAGS)
            
            items = list()
            
            if tags:
                for tag in tags:
                    item = CheckboxItem(tag)
                    item.title = tag
                    items.append(item)
                
            return items
        
        def get_items_count(self, session):
            return len(fetchItems(self, session, WBTypes.TAGS))

        def render_container_height(self, session):
            ''' scales-down the container height for lists that will never fill the max size '''
            height = self.container_height
            row_height = 18
            num_items = self.get_items_count(session)
            if num_items < self.items_per_page:
                height = height - ((self.items_per_page - num_items) * row_height)
            return "%dpx" % height
        
        def render_listcontainer_height(self, session):
            ''' scales-down the container height for lists that will never fill the max size '''
            height = self.listcontainer_height
            row_height = 18
            num_items = self.get_items_count(session)
            if num_items < self.items_per_page:
                height = height - ((self.items_per_page - num_items) * row_height) + 25
            return "%dpx" % height
            
        def render_title(self, session):
            return "Update tags"
              
    class NodeName(StringField):
        def __init__(self, app, name):
            super(EditNodeTagsForm.NodeName, self).__init__(app, name)

            self.input = self.DisabledInput(app, "input")
            self.replace_child(self.input)

        def get(self,session):
            value = self.input.get(session)
            return value
        
        def render_title(self, session):
            return "Host name"

        class DisabledInput(StringInput):
            pass

    class Tags(StringField):     
        def __init__(self, app, name):
            super(EditNodeTagsForm.Tags, self).__init__(app, name)

            self.input = self.DisabledInput(app, "input")
            self.replace_child(self.input)
                   
        def render_title(self, session):
            return "Current tags"
        
        def get(self,session):
            value = self.input.get(session)
            if not value or value == "":
                value = "No tags currently selected"
            return value
        
        def render_inputs(self, session, *args):
            '''
            Show the initial value passed-in, truncated to trunc_length characters
            '''
            value = self.input.get(session)
            value = truncate_text(value, 50, True)
            return value

        class DisabledInput(StringInput):
            pass

class EditTagNodesForm(ObjectFrameTaskForm):
    '''
    This form will allow the editing of nodes for a single given tag
    '''
    def __init__(self, app, name, task):
        super(EditTagNodesForm, self).__init__(app, name, task)

        self.tags = self.Tags(app, "tags")
        self.add_field(self.tags)
        
        self.node_name = self.NodeName(app, "node_name")
        self.add_field(self.node_name)
        
        self.possible_nodes = self.NodesList(app, "pnod")
        self.add_field(self.possible_nodes)
        
        self.update_enabled = False
        
                       
    def process_submit(self, session):
        tag = self.tags.input.get(session)
        nodes_value = self.possible_nodes.get(session)
        
        self.tags.validate(session)
        if not self.errors.get(session):
            self.tags.set(session, tag)
            
            self.task.invoke(session, None, tag, nodes_value)
            self.task.exit_with_redirect(session)

    def render_form_class(self, session):
        return " ".join((super(EditTagNodesForm, self).render_form_class(session), "mform"))
    
    class NodesList(PageableFilteredSelect):
        def __init__(self, app, name):
            super(EditTagNodesForm.NodesList, self).__init__(app, name)
            
        def render_items(self, session):
            items = self.do_get_items(session)
            nodes_string = ""
            
            given_tag = self.form.tags.input.param.get(session)
            selected_nodes = self.app.wallaby.get_node_names(given_tag)
            
            for i, node in enumerate(items):
                selected = ""
                if(selected_nodes and node.title in selected_nodes):
                    selected = " selected='selected' "
                nodes_string = nodes_string + "<option id='" + str(i) + "' name='" + node.title + "' value='" + node.title + "'" + selected + ">" + node.title + "</option>"
            
            return nodes_string
    
        def do_get_items(self, session):
            nodes = fetchItems(self, session, WBTypes.NODES)
            items = list()
            
            if nodes:
                for node in nodes:
                    item = CheckboxItem(node)
                    item.title = node
                    items.append(item)
                
            return items

        def get_items_count(self, session):
            return len(fetchItems(self, session, WBTypes.NODES))

        def render_container_height(self, session):
            ''' scales-down the container height for lists that will never fill the max size '''
            height = self.container_height
            row_height = 18
            num_items = self.get_items_count(session)
            if num_items < self.items_per_page:
                height = height - ((self.items_per_page - num_items) * row_height)
            return "%dpx" % height
        
        def render_listcontainer_height(self, session):
            ''' scales-down the container height for lists that will never fill the max size '''
            height = self.listcontainer_height
            row_height = 18
            num_items = self.get_items_count(session)
            if num_items < self.items_per_page:
                height = height - ((self.items_per_page - num_items) * row_height) + 25
            return "%dpx" % height
        
    
        def render_title(self, session):
            return "Update hosts"
              
    class NodeName(StringField):
        def __init__(self, app, name):
            super(EditTagNodesForm.NodeName, self).__init__(app, name)

            self.input = self.DisabledInput(app, "input")
            self.replace_child(self.input)
       
        def render_inputs(self, session, *args):
            value = ", ".join(self.app.wallaby.get_node_names(self.form.tags.get(session)))
            if not value or value =="":
                value = "No hosts currently selected"
            value = truncate_text(value, 50, True)
            return xml_escape(value)
        
        def render_title(self, session):
            return "Current hosts"

        class DisabledInput(StringInput):
            pass
        
    class Tags(StringField):         
        def __init__(self, app, name):
            super(EditTagNodesForm.Tags, self).__init__(app, name)

            self.input = self.DisabledInput(app, "input")
            self.replace_child(self.input)
               
        def render_title(self, session):
            return "Tag"
        
        def get(self,session):
            value = self.input.get(session)
            return value
        
        class DisabledInput(StringInput):
            pass
    
class EditTagFeaturesForm(ObjectFrameTaskForm):
    '''
    This form will allow the editing of nodes for a single given tag
    '''
    def __init__(self, app, name, task):
        super(EditTagFeaturesForm, self).__init__(app, name, task)

        self.tags = self.Tags(app, "tags")
        self.add_field(self.tags)
        
        self.feature_name = self.FeatureName(app, "feature_name")
        self.add_field(self.feature_name)
        
        self.possible_features = self.FeatureList(app, "pfeat")
        self.add_field(self.possible_features)
        
        self.update_enabled = False
        
                       
    def process_submit(self, session):
        tag = self.tags.input.get(session)
        features_value = self.possible_features.get(session)
        
        self.tags.validate(session)
        if not self.errors.get(session):
            self.tags.set(session, tag)
            
            self.task.invoke(session, None, tag, features_value)
            self.task.exit_with_redirect(session)

    def render_form_class(self, session):
        return " ".join((super(EditTagFeaturesForm, self).render_form_class(session), "mform"))
    
    class FeatureList(PageableFilteredSelect):
        def __init__(self, app, name):
            super(EditTagFeaturesForm.FeatureList, self).__init__(app, name)
            
        def render_items(self, session):
            items = self.do_get_items(session)
            features_string = ""
            
            given_tag = self.form.tags.input.param.get(session)
            tag_object = self.app.wallaby.get_tag_by_name(given_tag)
            selected_features = list()
            if tag_object is not None:
                selected_features = tag_object.features
            
            for i, feature in enumerate(items):
                selected = ""
                if(selected_features and feature.title in selected_features):
                    selected = " selected='selected' "
                features_string = features_string + "<option id='" + str(i) + "' name='" + feature.title + "' value='" + feature.title + "'" + selected + ">" + feature.title + "</option>"
            
            return features_string
    
        def do_get_items(self, session):
            features = fetchItems(self, session, WBTypes.FEATURES)
            items = list()
            
            if features:
                for feature in features:
                    item = CheckboxItem(feature)
                    item.title = feature
                    items.append(item)
                
            return items
        
        def get_items_count(self, session):
            return len(fetchItems(self, session, WBTypes.FEATURES))

        def render_container_height(self, session):
            ''' scales-down the container height for lists that will never fill the max size '''
            height = self.container_height
            row_height = 18
            num_items = self.get_items_count(session)
            if num_items < self.items_per_page:
                height = height - ((self.items_per_page - num_items) * row_height)
            return "%dpx" % height        
    
        def render_title(self, session):
            return "Update features"
              
    class FeatureName(StringField):
        def __init__(self, app, name):
            super(EditTagFeaturesForm.FeatureName, self).__init__(app, name)

            self.input = self.DisabledInput(app, "input")
            self.replace_child(self.input)
       
        def render_inputs(self, session, *args):
            tag = self.form.tags.get(session)
            value = ""
            tag_obj = self.app.wallaby.get_tag_by_name(tag)
            if tag_obj is not None:
                value = xml_escape(", ".join(tag_obj.features))
                if not value or value == "":
                    value = "No features currently selected"
                value = truncate_text(value, 50, True) 
            return value
        
        def render_title(self, session):
            return "Current features"

        class DisabledInput(StringInput):
            pass
        
    class Tags(StringField):         
        def __init__(self, app, name):
            super(EditTagFeaturesForm.Tags, self).__init__(app, name)

            self.input = self.DisabledInput(app, "input")
            self.replace_child(self.input)
               
        def render_title(self, session):
            return "Tag"
        
        def get(self,session):
            value = self.input.get(session)
            return value
        
        class DisabledInput(StringInput):
            pass    
    
class TagsNodeEditTask(ObjectFrameTask):
    '''
    On invocation, this task will take a node and reset the tags for that node to a 
    set of tags that are specified on the invocation
    '''
    def __init__(self, app, frame):
        super(TagsNodeEditTask, self).__init__(app, frame)

        self.form = EditNodeTagsForm(app, self.name, self)
        self.visible = False
        self.invoc = None

    def get_title(self, session):
        return "Change tags associated with this host"

    def do_enter(self, session, osession):
        self.form.tags.set(session, self.form.tags.get(osession))
        self.form.node_name.set(session, self.form.node_name.get(osession))

    def callback(self, result):
        if result == False:
            self.invoc.status = self.invoc.FAILED        
        self.invoc.end()
        self.app.wallaby.refresh(WBTypes.GROUPS,WBTypes.TAGS)

    def do_invoke(self, invoc, negotiator, node_name, tags):
        self.invoc = invoc
        try:
            call_async(self.callback, self.app.wallaby.edit_tags, node_name, *tags)
        except:
            invoc.status = invoc.FAILED
            log.debug("Edit node failed", exc_info=True)
            invoc.end()

class TagsTagEditTask(ObjectFrameTask):
    '''
    This is the task that will take a tag and a set of nodes and make the
    necessary assignments or unassignments.
    '''
    def __init__(self, app, frame):
        super(TagsTagEditTask, self).__init__(app, frame)

        self.form = EditTagNodesForm(app, self.name, self)
        self.invoc = None
        self.call_count = 0

    def get_title(self, session):
        return "Edit hosts"

    def do_enter(self, session, osession):
        tag_id = osession.values_by_path["main.grid.tag.id"]
        self.form.tags.set(session, tag_id)
        
        nodes = "No nodes currently assigned"
        node_list = self.app.wallaby.get_node_names(tag_id)
        if len(node_list) > 0:
            nodes = ", ".join(node_list)        
        self.form.node_name.set(session, nodes)

    def callback(self, result):
        if result is not None:                
            self.call_count -= 1
            if result == False:
                self.invoc.status = self.invoc.FAILED
            if(self.call_count <= 0):
                self.invoc.end()     
                self.app.wallaby.refresh(WBTypes.GROUPS,WBTypes.TAGS)   

    def do_invoke(self, invoc, negotiator, tag, chosen_nodes):
        '''
        Here we just kick off an async call that does the actual work for us
        '''
        self.invoc = invoc
        try:
            call_async(self.callback, self.make_calls, invoc, tag, chosen_nodes)
        except:
            self.call_count = 0
            invoc.status = invoc.FAILED
            log.debug("Edit tag failed", exc_info=True)
            invoc.end()
            
    def make_calls(self, invoc, tag, chosen_nodes):
        '''
        if the node is on the current_nodes list  and is on the chosen_nodes passed in, nothing to do
        ** if the node is NOT on the current_nodes list and is on the chosen_nodes passed in, add this tag to that node
        ** if the node is on the current_nodes list and is NOT on the chosen_nodes passed in, update that node sans this tag
        if the node is NOT on the current_nodes list and is NOT on the chosen_nodes passed in, nothing to do
        '''
        try:
            current_nodes = self.app.wallaby.get_node_names(tag)
            for node in chosen_nodes:
                if node not in current_nodes:
                    #we need to add the new tag to the existing tags for each node in the list
                    current_tags = self.app.wallaby.get_tag_names(node)                
                    current_tags.append(tag) 
                    self.call_count += 1                   
                    call_async(self.callback, self.app.wallaby.edit_tags, node, *current_tags)
            for node in current_nodes:
                if node not in chosen_nodes:
                    current_tags = self.app.wallaby.get_tag_names(node)
                    current_tags.remove(tag)
                    self.call_count += 1
                    call_async(self.callback, self.app.wallaby.edit_tags, node, *current_tags)
        except:
            self.call_count = 0
            invoc.status = invoc.FAILED
            log.debug("Edit tag failed", exc_info=True)
            invoc.end()
            return False
        return None        
        
        
class TagsFeatureEditTask(ObjectFrameTask):
    '''
    This is the task that will take a tag and a set of nodes and make the
    necessary assignments or unassignments.
    '''
    def __init__(self, app, frame):
        super(TagsFeatureEditTask, self).__init__(app, frame)

        self.form = EditTagFeaturesForm(app, self.name, self)
        self.invoc = None

    def get_title(self, session):
        return "Edit features"

    def do_enter(self, session, osession):
        tag_id = osession.values_by_path["main.grid.tag.id"]
        self.form.tags.set(session, tag_id)
        features = "No features currently assigned"
        tag = self.app.wallaby.get_tag_by_name(tag_id)
        feature_list = list()
        if tag is not None:
            feature_list = tag.features
        if len(feature_list) > 0:
            features = ", ".join(feature_list)        
        self.form.feature_name.set(session, features)        

    def callback(self, result):
        if result == False:
            self.invoc.status = self.invoc.FAILED        
        self.invoc.end()

    def do_invoke(self, invoc, negotiator, tag, chosen_features):
        '''
        if the node is on the current_nodes list  and is on the chosen_nodes passed in, nothing to do
        ** if the node is NOT on the current_nodes list and is on the chosen_nodes passed in, add this tag to that node
        ** if the node is on the current_nodes list and is NOT on the chosen_nodes passed in, update that node sans this tag
        if the node is NOT on the current_nodes list and is NOT on the chosen_nodes passed in, nothing to do
        '''
        self.invoc = invoc
        try:
            call_async(self.callback, self.app.wallaby.edit_features, tag, *chosen_features)
        except:
            invoc.status = invoc.FAILED
            log.debug("Edit feature failed", exc_info=True)
            invoc.end()        
        
class ActivateConfigTask(Task):        
    '''
    This task is used to activate the wallaby configuration.    
    '''           
    def __init__(self, app):
        super(ActivateConfigTask, self).__init__(app)
        cls = app.model.com_redhat_cumin_grid.Node 
        self.form = ActivateConfigurationForm(app, self.name, self, cls)
        self.invoc = None
        
    def get_title(self, session, object):
        return "Activate wallaby configuration"
    
    def callback(self, results):
        if len(results[0]) != 0 or len(results[1]) != 0:
            self.invoc.status = self.invoc.FAILED 
        self.invoc.end()
    
    def do_invoke(self, session, object, invoc):
        self.invoc = invoc        
        try:
            call_async(self.callback, self.app.wallaby.activate_configuration)
        except:
            invoc.status = invoc.FAILED
            log.debug("Activate config failed", exc_info=True)
            invoc.end()
        
class AddTags(Task):     
    '''
    This task is used to create a tag in wallaby without assigning it to any nodes.    
    '''           
    def __init__(self, app):
        super(AddTags, self).__init__(app)
        cls = app.model.com_redhat_cumin_grid.Node 
        self.form = CreateTags(app, self.name, self, cls)
        self.invoc = None
        
    def get_title(self, session, object):
        return "Create tags"

    def callback(self, result):
        if result == False:
            self.invoc.status = self.invoc.FAILED
        self.app.wallaby.refresh(WBTypes.GROUPS,WBTypes.TAGS)
        self.invoc.end()
        
        
    def do_invoke(self, session, object, invoc, tag):
        self.invoc = invoc
        tags = [x.strip() for x in tag.split(',')]

        try:
            call_async(self.callback, self.app.wallaby.create_tags, tags)      
        except:
            invoc.status = invoc.FAILED
            log.debug("Adding tags failed", exc_info=True)
            invoc.end()
        
class RemoveNodeTags(ObjectSelectorTask):    
    '''
    This is the task that is invoked to trigger the deletion of a given tag.  
    It will call WallabyOperations.remove_tag, which in turn will remove the tag from
    all nodes it is currently associated with and then will remove the tag from wallaby entirely.
    '''            
    def __init__(self, app, selector, name):
        super(RemoveNodeTags, self).__init__(app, selector)
        cls = app.model.com_redhat_cumin_grid.Node 
        self.form = RemoveTags(app, self.name, self, cls)
        self.invoc = None
        
    def get_title(self, session):
        return "Delete tags"
    
    def invoke(self, session, selection):
            self.invoc = self.start(session, selection)
            selection = [unescape_entity(text) for text in selection]
            try:
                self.do_invoke(self.invoc, selection)
            except Exception, e:
                self.invoc.exception = e
                self.invoc.status = self.invoc.FAILED
                self.invoc.end()    
    
    def callback(self, result):
        if result == False:
            self.invoc.status = self.invoc.FAILED        
        self.app.wallaby.refresh()
        self.invoc.end()
        
    
    def do_invoke(self, invoc, tags):
        try:
            call_async(self.callback, self.app.wallaby.remove_tags, tags)
        except:
            invoc.status = invoc.FAILED
            log.debug("Remove node tags failed", exc_info=True)
        
    def get_item_content(self, session, item):
        return xml_escape(item)
  
def fetchItems(self, session, type):
        '''
        fetch the list of <type> from wallaby
        '''
        wallaby_items = self.app.wallaby.get_data(type)
        item_list = list()
        
        for item in wallaby_items:
            item_list.append(xml_escape(str(item.name)))
        item_list.sort()
    
        return item_list    
