from wooly.util import StringCatalog, Writer
import logging
from cumin.objectframe import ObjectFrame, ObjectFrameTask,\
    ObjectFrameTaskForm
from cumin.objectselector import ObjectSelector, ObjectLinkColumn,\
    MonitorSelfStatColumn, ObjectTable, MonitorSelfAgeColumn, SelectableSearchObjectTable
from wooly import Widget, Attribute, Parameter
from parsley.stringex import rpartition
from cumin.parameters import RosemaryObjectParameter
from wooly.parameters import ListParameter, StringParameter
from wooly.template import WidgetTemplate
from cumin.stat import StatFlashChart
from sage.util import call_async

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.grid.negotiator")

class NegotiatorFrame(ObjectFrame):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Negotiator

        super(NegotiatorFrame, self).__init__(app, name, cls)

class NegotiatorSelector(ObjectSelector):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Negotiator

        super(NegotiatorSelector, self).__init__(app, name, cls)

        frame = "main.grid.negotiator"
        col = ObjectLinkColumn(app, "name", cls.Name, cls._id, frame)
        self.add_column(col)

        self.add_attribute_column(cls.Machine)
        self.add_attribute_column(cls.System)

        stat = MonitorSelfAgeColumn(app, cls.MonitorSelfAge.name, cls.MonitorSelfAge)
        self.add_column(stat)
        stat = MonitorSelfStatColumn(app, cls.MonitorSelfCPUUsage.name, cls.MonitorSelfCPUUsage)
        self.add_column(stat)
        stat = MonitorSelfStatColumn(app, cls.MonitorSelfImageSize.name, cls.MonitorSelfImageSize)
        self.add_column(stat)

        self.field_param = StringParameter(app, "field_param")
        self.add_parameter(self.field_param)
        
        self.select_input = self.NegotiatorFieldOptions(app, self.field_param)
        self.add_selectable_search_filter(self.select_input)

        #self.start = DaemonSelectionStart(app, self, "NEGOTIATOR")
        #self.stop = DaemonSelectionStop(app, self, "NEGOTIATOR")

        self.enable_csv_export()

    def create_table(self, app, name, cls):
        # avoid the checkboxes
        return SelectableSearchObjectTable(app, name, cls)
    
    class NegotiatorFieldOptions(SelectableSearchObjectTable.SearchFieldOptions):
        def __init__(self, app, param):
            super(NegotiatorSelector.NegotiatorFieldOptions, self).__init__(app, param)
            self.cls = app.model.com_redhat_grid.Negotiator
            
        def do_get_items(self, session):
            return [self.cls.Name, self.cls.Machine, self.cls.MonitorSelfAge, \
                    self.cls.MonitorSelfCPUUsage, self.cls.MonitorSelfImageSize, self.cls.System]

class GroupHelper(Widget):
    def __init__(self, app, name, negotiator):
        super(GroupHelper, self).__init__(app, name)

        self.negotiator = negotiator

        self.info = Attribute(app, "info")
        self.add_attribute(self.info)

        self.results = Attribute(app, "results")
        self.add_attribute(self.results)

    def get_config_info(self, session):
        info = self.info.get(session)

        if not info:
            negotiator = self.negotiator.get(session)
            info = self.get_group_info(session, negotiator)
            self.info.set(session, info)

        return info

    def get_group_info(self, session, negotiator):
        results = self.app.model.get_negotiator_group_names(negotiator)
        groups = results.data
        info = dict()

        if not results.exception:
            try:
                groups = self.split_group_names(groups)
            except:
                groups = []

            if groups:
                for group in groups:
                    info[group] = dict()

        self.results.set(session, results)

        return info

    def get_results(self, session):
        return self.get_config_info(session)

    def has_child(self, session, group):
        info = self.get_config_info(session)

        try:
            return info[group]['has_child']
        except KeyError:
            info[group]['has_child'] = False
            for key in info:
                if key.startswith(group+"."):
                    info[group]['has_child'] = True
                    break

        self.info.set(session, info)
        return info[group]['has_child']

    def get_parent(self, session, group):
        info = self.get_config_info(session)

        try:
            return info[group]['parent']
        except KeyError:
            parent = ""
            for key in info:
                if key != group and group.startswith(key):
                    if len(key) > len(parent):
                        parent = key

            info[group]['parent'] = parent

        self.info.set(session, info)
        return info[group]['parent']

    def get_siblings(self, session, node):
        info = self.get_config_info(session)

        siblings = list()
        (ng, _, _) = rpartition(node, ".")
        for group in info:
            (g, _, _) = rpartition(group, ".")
            if g == ng:
                siblings.append(group)

        return siblings

    def get_group_names(self, session):
        info = self.get_config_info(session)
        return list(info)

    def split_group_names(self, group_string):
        g_string = group_string.replace(", ", ",")
        if not "," in g_string:
            return g_string.split()
        return  g_string.split(",")

    def get_config_for_groups(self, session, config, groups):
        info = self.get_config_info(session)

        needed_groups = [x for x in groups if not config in info[x]]

        if len(needed_groups) > 0:
            negotiator = self.negotiator.get(session)

            dynamic_results, static_results = self.app.model.get_negotiator_config_values(negotiator, needed_groups, config)
            if(config == "GROUP_QUOTA_DYNAMIC"):
                raw_configs = dynamic_results.data
            else:
                raw_configs = static_results.data

            try:
                for config in raw_configs:
                    for group in raw_configs[config]:
                        if raw_configs[config][group].error:
                            info[group][config] = ""  ##raw_configs[config][group].error
                        elif raw_configs[config][group].got_data:
                            info[group][config] = raw_configs[config][group].data['Value']
            except:
                log.debug("Problem getting group config info", exc_info=True)

            self.info.set(session, info)
        return info

    def get_config_value(self, session, group, config):
        info = self.get_config_info(session)
        try:
            return info[group][config]
        except KeyError:
            try:
                info = self.get_config_for_groups(session, config, [group])
                return info[group][config]
            except:
                return self.loading_indicator()

    def loading_indicator(self):
        return  "<em>loading</em>"

    def get_unclaimed_dyn_quota(self, session, groups):
        info = self.get_config_info(session)
        total = 0.0
        for group in groups:
            try:
                value = info[group]["GROUP_QUOTA_DYNAMIC"]
            except KeyError:
                info = self.get_config_for_groups(session, "GROUP_QUOTA_DYNAMIC", [group])
            try:
                total = total + float(value)
            except:
                pass

        val = 1.0 - total
        val = max(0, val)
        val = min(1.0, val)
        return val

class GroupForm(ObjectFrameTaskForm):
    def __init__(self, app, name, task):
        super(GroupForm, self).__init__(app, name, task)

        cls = app.model.com_redhat_grid.Negotiator
        self.negotiator = RosemaryObjectParameter(app, "neg", cls)
        self.add_parameter(self.negotiator)

        self.group_helper = GroupHelper(app, "groups", self.negotiator)
        self.add_child(self.group_helper)

        group_name = Parameter(app, "gn")
        self.group_names = ListParameter(app, "group_names", group_name)
        self.add_parameter(self.group_names)

        original_value = Parameter(app, "ov")
        self.original_values = ListParameter(app, "original_values", original_value)
        self.add_parameter(self.original_values)

        self.buttons = list()

        #self.defer_enabled = True

    def render_group_name(self, session, group):
        return group

    def render_group_name_path(self, session, group):
        return self.group_names.path

    def render_original_value_path(self, session, group):
        return self.original_values.path

class EditDynamicQuotaForm(GroupForm):
    def __init__(self, app, name, task):
        super(EditDynamicQuotaForm, self).__init__(app, name, task)

        self.field_tmpl = WidgetTemplate(self, "field_html")
        self.unclaimed_tmpl = WidgetTemplate(self, "unclaimed_html")

        quota = Parameter(app, "quota")
        self.add_parameter(quota)

        self.quotas = ListParameter(app, "quotas", quota)
        self.add_parameter(self.quotas)

        self.group_leader = Parameter(app, "group_leader")
        self.add_parameter(self.group_leader)

        self.chart = PriorityPieChart \
            (app, "chart", self.object, self.group_helper, self.group_leader)
        self.add_child(self.chart)

    def render_title(self, session):
        return "Edit Dynamic Group Quota"

    def render_submit_content(self, session):
        return "Change percentage"

    def render_form_class(self, session):
        return "priorityForm"

    def render_data_col_header(self, session):
        return "Percent"
    
    def render_all_group_values(self, session):
        group_leader = self.group_leader.get(session)
        groups = self.group_helper.get_siblings(session, group_leader)
        info = self.group_helper.get_config_for_groups(session, "GROUP_QUOTA_DYNAMIC", groups)
        values = []
        dynamic_groups = []
        try:
            dynamic_groups = ["%s" % x for x in groups if info[x]["GROUP_QUOTA_DYNAMIC"] != ""]
        except:
            log.error("Error when loading dynamic group values for quota editing.")
        for group in sorted(groups):
            if(group in dynamic_groups):
                values.append(self.render_quota_value(session, group))      
        
       # values.reverse()
        values.append(self.render_unclaimed_value(session, "Unclaimed"))
                
        return values

    def render_all_group_names(self, session):
        group_leader = self.group_leader.get(session)
        groups = self.group_helper.get_siblings(session, group_leader)
        info = self.group_helper.get_config_for_groups(session, "GROUP_QUOTA_DYNAMIC", groups)
        values = []
        dynamic_groups = []
        try:
            dynamic_groups = ["%s" % x for x in groups if info[x]["GROUP_QUOTA_DYNAMIC"] != ""]
        except:
            log.error("Error when loading dynamic group names for quota editing.")
        for group in sorted(groups):
            if(group in dynamic_groups):
                values.append(group)      
        
        values.append("Unclaimed")
                
        return values
    
    def render_groups(self, session):
        writer = Writer()
                
        group_leader = self.group_leader.get(session)
        groups = self.group_helper.get_siblings(session, group_leader)
        info = self.group_helper.get_config_for_groups(session, "GROUP_QUOTA_DYNAMIC", groups)
        dynamic_groups = []
        try:
            dynamic_groups = ["%s" % x for x in groups if info[x]["GROUP_QUOTA_DYNAMIC"] != ""]
        except:
            log.error("Error when loading dynamic groups for quota editing.")
        for group in sorted(groups):
            if(group in dynamic_groups):
                self.field_tmpl.render(writer, session, group)

        self.unclaimed_tmpl.render(writer, session, "Unclaimed")

        return writer.to_string()

    def render_quota_name(self, session, group):
        return self.quotas.path

    def render_quota_value(self, session, group):
        value = self.group_helper.get_config_value(session, group, "GROUP_QUOTA_DYNAMIC")
        try:
            return round(float(value) * 100.0, 2)
        except:
            return 0.0

    def render_unclaimed_value(self, session, group):
        group_leader = self.group_leader.get(session)
        groups = self.group_helper.get_siblings(session, group_leader)
        unclaimed = self.group_helper.get_unclaimed_dyn_quota \
            (session, groups)
        return round(float(unclaimed) * 100.0, 2)

    def render_chart_id(self, session):
        return self.chart.render_id(session)

    def _invoke_tasks(self, session):
        negotiator = self.negotiator.get(session)
        quotas = self.quotas.get(session)
        group_names = self.group_names.get(session)
        original_values = self.original_values.get(session)
        info = self.group_helper.get_config_info(session)

        changed = False
        for group, new_value, original_value in zip(group_names, quotas, original_values):
            if group == "Unclaimed":
                continue
            quota = self.check_quota(new_value, original_value)
            if quota:
                self.task.invoke(session, negotiator,
                                 "GROUP_QUOTA_DYNAMIC_" + group, quota)
                info[group]["GROUP_QUOTA_DYNAMIC"] = quota
                changed = True

        if changed:
            self.task.reconfig(negotiator)
            self.app.model.update_negotiator_config_value(negotiator)

    def process_submit(self, session):
        call_async(None, self._invoke_tasks, session)
        self.task.exit_with_redirect(session)

    def check_quota(self, quota, original):
        try:
            pri = float(quota)
        except:
            return None
        if pri < 0.0 or pri > 100.0:
            return '0'

        try:
            original = float(original)
        except:
            original = 0
        if pri == original:
            return None

        return str(pri / 100)

class PriorityPieChart(StatFlashChart):
    def __init__(self, app, name, negotiator, group_helper, group_leader):
        super(PriorityPieChart, self).__init__(app, name, negotiator)

        self.negotiator = negotiator

        self.chart_type = "pie"
        self.fullpageable = False
        self.update_enabled = False

        self.group_helper = group_helper
        self.group_leader = group_leader

    def render_title(self, session):
        pass

    def render_duration(self, session):
        pass

    def render_width(self, session):
        return 360

    def render_height(self, session):
        return 210

class NegotiatorGroupTask(ObjectFrameTask):
    def do_exit(self, session):
        self.app.main_page.main.grid.view.show(session)

    def do_invoke(self, invoc, negotiator, group, value):
        try:
            short_group = group.split("_")[-1]
        except:
            short_group = group
        invoc.description = "Set %s to %s" % (short_group, value)
        result = self.app.remote.set_raw_config(negotiator, group, value)
        if result.error:
            raise result.error

        invoc.status_code = result.status
        invoc.end()

    def reconfig(self, negotiator):
        self.app.remote.reconfig(negotiator)

class NegotiatorEditDynamicQuota(NegotiatorGroupTask):
    def __init__(self, app, frame):
        super(NegotiatorEditDynamicQuota, self).__init__(app, frame)

        self.form = EditDynamicQuotaForm(app, self.name, self)
        # don't show in page summary section
        self.visible = False

    def get_title(self, session):
        return ""

    def get_description(self, session):
        return "Edit dynamic quota"

    def do_enter(self, session, osession):
        group_leader = self.form.group_leader.get(osession)
        self.form.group_leader.set(session, group_leader)

        negotiator = self.frame.negotiator_attribute.get(osession)
        self.form.negotiator.set(session, negotiator)

