import logging

from wooly import Widget, Attribute
from wooly.util import StringCatalog, Writer
from wooly.datatable import DataAdapterOptions, DataAdapterField
from wooly.table import TableHeader
from wooly.widgets import RadioModeSet, WidgetSet
from wooly.template import WidgetTemplate
from wooly.forms import StringInput

from parsley.stringex import rpartition
from rosemary.sqlquery import SqlQueryOptions

from cumin.sqladapter import ObjectSqlAdapter
from cumin.stat import StatSet, PieChartPage, StatFlashChart, ReportingChart
from cumin.objectselector import ObjectSelector, MonitorSelfStatColumn, ObjectTableColumn, ObjectTable,\
    ObjectLinkColumn, CsvStatsExporter, ExportButton, MonitorSelfAgeColumn
from cumin.parameters import YoungestAttribute
from cumin.util import rgb_to_string, xml_escape

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.dashboard")

class PoolDashboard(RadioModeSet):
    def __init__(self, app, name, collector):
        super(PoolDashboard, self).__init__(app, name)

        self.collector = collector

        dashboard = DashboardSummary(app, "d", collector)
        self.add_tab(dashboard)

        performance = DashboardPerformance(app, "p")
        self.add_tab(performance)

        capacity = DashboardCapacity(app, "c")
        self.add_tab(capacity)
        
        history = DashboardHistory(app, "h")
        self.add_tab(history)

    def render_title(self, session):
        return "Overview"

class DashboardHistory(Widget):
    def __init__(self, app, name):
        super(DashboardHistory, self).__init__(app, name)
        
        charts = WidgetSet(app, "charts")
        self.add_child(charts)
        
        chart = self.PoolEfficiencyChart(app, "eff", app.model.com_redhat_grid_plumage.OSUtil)
        chart.stats = ["efficiency"]
        chart.max_samples = 250
        chart.duration.param.default = "86400"
        charts.add_child(chart)   

        chart = self.PoolMemoryChart(app, "fmem", app.model.com_redhat_grid_plumage.OSUtil)
        chart.stats = ["usedmem", "freemem"]
        chart.max_samples = 250
        chart.duration.param.default = "86400"
        charts.add_child(chart)
        
        chart = self.PoolCpuChart(app, "fcpu", app.model.com_redhat_grid_plumage.OSUtil)
        chart.stats = [ "usedcpu", "freecpu"]
        chart.max_samples = 250
        chart.duration.param.default = "86400"
        charts.add_child(chart)
        
        chart = self.UserUsageChart(app, "useruse", app.model.com_redhat_grid_plumage.Accountant)
        chart.stats = ["resused"]
        chart.max_samples = 250
        filter = ReportingChart.FilterInput(app, "namefilter", app.model.com_redhat_grid_plumage.Accountant, app.model.com_redhat_grid_plumage.Accountant.user.name, "userc", "Filter user")
        chart.filters.append(filter)
        chart.add_child(filter)
        chart.duration.param.default= "86400"
        charts.add_child(chart)

    def render_title(self, session):
        return "History"
    
    class PoolMemoryChart(ReportingChart):
        def render_title(self, session):
            return "Pool memory"
        
    class PoolCpuChart(ReportingChart):
        def render_title(self, session):
            return "Pool cpus"        
    
    class PoolEfficiencyChart(ReportingChart):
        def render_title(self, session):
            return "Pool efficiency"    

    class UserUsageChart(ReportingChart):
        def render_title(self, session):
            return "Pool usage by accounting group"

    class AccountingChart(ReportingChart):
        def render_title(self, session):
            return "Usage by parent accounting group"         
               
class DashboardSummary(Widget):
    def __init__(self, app, name, collector):
        super(DashboardSummary, self).__init__(app, name)

        job_data = DashboardOverviewJobSummary(app, "job_info")
        self.add_child(job_data)

        slot_data = GridSlotsSummary(app, "host_info", collector)
        self.add_child(slot_data)

        neg_through = NegotiatorJobThroughput(app, "negotiator_throughput")
        self.add_child(neg_through)

        cls = app.model.com_redhat_grid.Scheduler
        # tell the DashboardSummaryStats to average this column
        setattr(cls.MeanTimeToStart, "average", True)

        columns = (cls.JobSubmissionRate, cls.JobStartRate, cls.JobCompletionRate, cls.MeanTimeToStart)
        stats = FootnoteDashboardSummaryStats(app, "scheduler_info", cls, columns, "Scheduler.Jobs")
        stats.title = "Job scheduler info"
        self.add_child(stats)

    def render_title(self, session):
        return "Summary"

class DashboardPerformance(Widget):
    def __init__(self, app, name):
        super(DashboardPerformance, self).__init__(app, name)

        cls = app.model.com_redhat_grid.Collector
        coll = YoungestAttribute(app, "coll", cls)
        c = MonitorSelfStats(app, "ms_c", cls, "Collector performance", None, coll)
        self.add_child(c)

        cls = app.model.com_redhat_grid.Negotiator
        frame = "main.grid.negotiator"
        neg =  YoungestAttribute(app, "neg", cls)
        n = MonitorSelfStats(app, "ms_n", cls, "Negotiator performance", frame, neg)
        self.add_child(n)

        s = SchedulerPerformance(app, "ms_s")
        self.add_child(s)

    def render_title(self, session):
        return "Performance"

class DashboardCapacity(Widget):
    def __init__(self, app, name):
        super(DashboardCapacity, self).__init__(app, name)

        capacity = DashboardCapacitySlotSummary(app, "slot_capacity")
        self.add_child(capacity)

        os_data = GridOSBreakdown(app, "os_breakdown")
        self.add_child(os_data)
        
        chart = self.UtilChart(app, "util", app.model.com_redhat_grid_plumage.OSUtil)
        chart.stats = ["total", "unused", "owner", "used"]
        chart.max_samples = 250
        chart.duration.param.default = "3600"
        self.add_child(chart)

    def render_title(self, session):
        return "Slot capacity"
    
    class UtilChart(ReportingChart):
        def render_title(self, session):
            return "Slot utilization"

class DefinitionSet(StatSet):
    def __init__(self, app, name, object, title):
        super(DefinitionSet, self).__init__(app, name, object)

        exporter = CsvStatsExporter(self.app, self.name + "_csv", (object,), self)

        self.export = ExportButton(self.app, "export", (object,), exporter, title)
        self.add_child(self.export)

    def render_html_title(self, session, item):
        unit = item.unit and " (%s)" % item.unit or ""
        description = item.description and item.description or "%s from the %s table" % (item.name, item.cls._name)
        return "%s%s" % (description, unit)

# Displays a pie chart and a set of stats as the legend
# The legend is a definition list with the dt being the stat name
# and the dd being the value
# Supports a stat being marked as a "Totals" line, in which case
# the stat isn't put in the pie chart
class PieStatSet(DefinitionSet):
    radius = 60
    def __init__(self, app, name, object, title="stats"):
        super(PieStatSet, self).__init__(app, name, object, title)

        self.color_scheme = PieChartPage.RAINBOW

        # determines if a line is drawn under the legend
        self.has_total = False
        self.has_pie_chart = True

        # if this gets defined, this widget will have a link to display
        # the chart in a popup
        self.chart_link = None
        self.popup_chart = self.DefinitionSetPopup(app, "popup_chart")
        self.add_child(self.popup_chart)
        
        self.pie_width = "150px"
        self.pie_height = "150px"

        self.pie_tmpl = WidgetTemplate(self, "pie_html")

    def do_render(self, session):
        # don't show this if our object isn't there
        # Some of our children depend on an object, and some
        # have overloaded do_get_items to read different data,
        # so if self.object has been set to None skip the check.
        if self.object:
            if not self.object.get(session):
                return
        return super(PieStatSet, self).do_render(session)

    # we generate the style sheet for the legend based on
    # the colors defined in the PieChartPage
    def render_legend_styles(self, session):
        colors = PieChartPage.color_schemes[self.color_scheme]
        styles = list()
        for color in colors:
            hx = rgb_to_string(*color)
            styles.append(".DefinitionSet dt.legend%s span { background-color: #%s;}" % (hx, hx))
        return "\n".join(styles)

    # don't put a line under the legend if there is a total
    def render_class(self, session):
        cls = super(PieStatSet, self).render_class(session)
        return "%s%s" % (cls, self.has_total and " hastotal" or "")

    def is_total(self, item):
        return False

    # the color block next to each legend line is based on the class 
    def render_legend_class(self, session, item):
        cls = ""
        if self.is_total(item):
            cls = "total"
        else:
            cls = self.get_legend_class(session, item)
        return cls

    def render_dd_class(self, session, item):
        dt_class = self.render_legend_class(session, item)
        return "total" is dt_class and " class=\"total\"" or ""

    def render_popup_chart(self, session):
        if self.chart_link:
            return self.popup_chart.render(session)

    def render_chart(self, session):
        if self.has_pie_chart:
            writer = Writer()
            self.pie_tmpl.render(writer, session)

            return writer.to_string()

    def render_pie_src(self, session):
        slices = self.get_pie_slices(session)
        return PieChartPage.get_href(slices, self.color_scheme, self.radius)
    
    def render_pie_slices(self, session):
        items = self.do_get_items(session)
        return [int(self.get_item_value(session, x)) or 0 for x in items if not self.is_total(x)]

    def render_width(self, session):
        return self.radius * 2

    def render_height(self, session):
        return self.render_width(session)

    def get_pie_slices(self, session):
        # don't include total lines, convert None to 0
        items = self.do_get_items(session)
        return [self.get_item_value(session, x) or 0 for x in items if not self.is_total(x)]
    
    def render_id_nodots(self, session):
        return self.render_id(session).replace(".", "_")
    
    def render_pie_width(self, session):
        if self.has_pie_chart:
            return self.pie_width
        else:
            return "0px"
    
    def render_pie_height(self, session):
        if self.has_pie_chart:
            return self.pie_height
        else:
            return "0px"
        
    def render_colors(self, session):
        colors = PieChartPage.color_schemes[self.color_scheme]
        color_list = ["#%s" % rgb_to_string(*color) for color in colors]
        return color_list       

    class DefinitionSetPopup(Widget):
        def render_chart_href(self, session):
            return self.page.get_popup_url(session, self.parent.chart_link)

        def render_title(self, session):
            return self.parent.render_title(session)

class AliasSqlColumn(object):
    def __init__(self, identifier, alias):
        self.identifier = identifier
        self.alias = alias

class MinimalTable(ObjectTable):
    def __init__(self, app, name, cls):
        super(MinimalTable, self).__init__(app, name, cls)

        # no font or page control
        self.header = self.MinimalTableHeader(app, "header")
        self.replace_child(self.header)

        # no checkboxes or id field
        self.adapter = self.MinimalAdapter(app, cls)

    class MinimalAdapter(ObjectSqlAdapter):
        def get_id_field(self, cls):
            return None

    class MinimalTableHeader(TableHeader):
        def __init__(self, app, name):
            super(MinimalTable.MinimalTableHeader, self).__init__(app, name)

            self.font = Attribute(app, "font")
            self.font.default = 0.9
            self.add_attribute(self.font)

            self.limit = Attribute(app, "limit")
            self.limit.default = 25
            self.add_attribute(self.limit)

            self.offset = Attribute(app, "offset")
            self.offset.default = 0
            self.add_attribute(self.offset)

# The following columns and fields should probably be moved
# to a more general location
class DerivedTableColumn(ObjectTableColumn):
    def __init__(self, app, name):
        super(DerivedTableColumn, self).__init__(app, name, None)

    def init(self):
        # avoid ObjectTableColumn's init() since we are setting up our own field
        super(ObjectTableColumn, self).init()

        self.field = self.get_field()

    def get_field(self):
        raise "Not Implemented"

class QuotientSqlField(DataAdapterField):
    def __init__(self, adapter, name, attr1, attr2, title=None):
        super(QuotientSqlField, self).__init__(adapter, name, float)

        self.title = title and title or name

        # attr1 and 2 could be strings or they could be rosemary attributes
        try:
            id1 = attr1.sql_column.identifier
        except AttributeError:
            id1 = attr1
        try:
            id2 = attr2.sql_column.identifier
        except AttributeError:
            id2 = attr2

        # avoid divide by 0 by using nullif
        nullif = "NULLIF(%s,0)" % id2
        identifier = "(%s/%s)" % (id1, nullif)

        # we need an alias if we sort on this column
        alias = self.name
        self.column = AliasSqlColumn(identifier, alias)

        self.adapter.columns.append(self.column)
        self.format = "%0.02f%%"

    def get_title(self, session):
        return self.title

class SumSqlField(DataAdapterField):
    def __init__(self, adapter, name, attr, title=None):
        super(SumSqlField, self).__init__(adapter, name, float)

        self.title = title and title or name

        identifier = "sum(%s)" % (attr.sql_column.identifier)

        # we need an alias if we sort on this column
        alias = self.name
        self.column = AliasSqlColumn(identifier, alias)

        self.adapter.columns.append(self.column)

    def get_title(self, session):
        return self.title

# Create a sortable column that is the quotient of two extisting columns
class QuotientSqlColumn(DerivedTableColumn):
    def __init__(self, app, name, attr1, attr2):
        super(QuotientSqlColumn, self).__init__(app, name)

        self.attr1 = attr1
        self.attr2 = attr2
        self.title = name

    def get_field(self):
        return QuotientSqlField(self.table.adapter, self.name, self.attr1, self.attr2, self.title)

    def init(self):
        super(QuotientSqlColumn, self).init()

        # change quotient into a percent
        self.field.column.identifier = "%s*100" % self.field.column.identifier

# Create a sortable column that is the sum of two extisting columns
class SumSqlColumn(DerivedTableColumn):
    def __init__(self, app, name, attr, title):
        super(SumSqlColumn, self).__init__(app, name)

        self.attr = attr
        self.title = title
        self.format_method = getattr(attr, "unit", None)

    def get_field(self):
        field = SumSqlField(self.table.adapter, self.name, self.attr, self.title)
        if self.format_method:
            if self.format_method == "MiB":
                format_method = self.fmt_mb
            elif self.format_method == "KiB":
                format_method = self.fmt_kb
            else:
                format_method = self.fmt_b

            field.format = format_method
        return field

class DashboardSumData(ObjectSqlAdapter):
    def __init__(self, app, columns, cls):
        super(DashboardSumData, self).__init__(app, cls)

        for column in columns:
            col = "sum(\"%s\")" % column
            self.columns.append(col)
        # add a count field so we can calculate averages
        self.columns.append("count(1)")

    def get_id_field(self, cls):
        return None

    def get_record(self, session):
        values = dict()
        options = DataAdapterOptions()
        options.offset = 0

        records = self.get_data(values, options)

        return records[0]

class DashboardSummaryStats(DefinitionSet):
    def __init__(self, app, name, cls, columns, title):
        super(DashboardSummaryStats, self).__init__(app, name, None, title)

        self.record = Attribute(app, "totals")
        self.add_attribute(self.record)

        self.columns = columns
        self.sum_columns = [x.name for x in columns]
        self.sum_cls = cls
        self.data = DashboardSumData(app, self.sum_columns, self.sum_cls)

        self.title = None

    def render_title(self, session):
        return self.title

    def do_get_items(self, session):
        return self.columns

    def render_item_title(self, session, item):
        return item.title

    def get_item_value(self, session, item):
        record = self.get_record(session)
        value = record[self.get_item_index(item)] or 0

        # if we want to show an average instead of an aggregate
        if getattr(item, "average", None):
            # the count of records is tucked away past the end of the normal fields
            total = record[len(self.columns)]
            if total:
                value = value / total
            else:
                value = 0
        return value

    def get_item_index(self, item):
        return self.sum_columns.index(item.name)

    def get_record(self, session):
        record = self.record.get(session)
        if not record:
            record = self.data.get_record(session)
            self.record.set(session, record)

        return record

class FootnoteDashboardSummaryStats(DashboardSummaryStats):
    def __init__(self, app, name, cls, columns, title):
        super(FootnoteDashboardSummaryStats, self).__init__(app, name, cls, columns, title)

        self.footnote_data = DashboardSumData(app, [cls.WindowedStatWidth.name], cls)

    def render_footnote_value(self, session):
        # get the average WindowedStarWidth for all schedulers
        data = self.footnote_data.get_record(session)
        try:
            value = data[0] / data[1]
        except:
            value = 0
        return value

class DashboardPieSummarySet(PieStatSet):
    def __init__(self, app, name, cls, columns, title):
        super(DashboardPieSummarySet, self).__init__(app, name, None, title)

        self.record = Attribute(app, "totals")
        self.add_attribute(self.record)

        # XXX - consider using an ObjectSelector with SumSqlColumns as the data source
        self.columns = columns
        self.sum_columns = [x.name for x in columns]
        self.sum_cls = cls
        self.data = DashboardSumData(app, self.sum_columns, self.sum_cls)

        self.has_total = True
        self.color_scheme = PieChartPage.BLUES

    def do_get_items(self, session):
        return self.columns

    def get_item_index(self, item):
        return self.sum_columns.index(item.name)

    def is_total(self, item):
        index = self.get_item_index(item)
        return index == len(self.sum_columns) - 1

    def render_item_title(self, session, item):
        return item.title

    def get_item_value(self, session, item):
        record = self.get_record(session)
        return record[self.get_item_index(item)] or 0

    def get_legend_class(self, session, item):
        index = self.get_item_index(item)
        return "legend%s" % rgb_to_string(*(PieChartPage.color_schemes[self.color_scheme][index]))

    def get_record(self, session):
        record = self.record.get(session)
        if not record:
            record = self.data.get_record(session)
            self.record.set(session, record)

        return record

class DashboardOverviewJobSummary(DashboardPieSummarySet):
    def __init__(self, app, name):
        cls = app.model.com_redhat_grid.Scheduler
        columns = [cls.TotalRunningJobs, cls.TotalHeldJobs, cls.TotalIdleJobs,
                   cls.TotalRemovedJobs, cls.TotalJobAds]

        super(DashboardOverviewJobSummary, self).__init__(app, name, cls, columns, "scheduler.jobs")

        self.color_scheme = PieChartPage.GREENS

    def render_title(self, session):
        return "Job info"

class DashboardCapacitySlotSummary(DashboardPieSummarySet):
    PERCENT_COLUMN = "% Memory used"
    def __init__(self, app, name):
        self.cls = app.model.com_redhat_grid.Slot
        columns = [self.cls.Disk, self.cls.ImageSize, self.cls.Memory]

        super(DashboardCapacitySlotSummary, self).__init__(app, name, self.cls, columns, "slot.summary")

        self.has_pie_chart = False
        self.has_total = False

    def render_title(self, session):
        return "Slot capacity"

    def do_get_items(self, session):
        cols = list(self.columns)
        cols.append(self.PERCENT_COLUMN)
        return cols

    def get_item_index(self, item):
        if item is self.PERCENT_COLUMN:
            return 0
        return super(DashboardCapacitySlotSummary, self).get_item_index(item)

    def is_total(self, item):
        return False

    def render_item_title(self, session, item):
        if item is self.PERCENT_COLUMN:
            return self.PERCENT_COLUMN
        return item.title

    def get_item_value(self, session, item):
        record = self.get_record(session)
        if item is self.PERCENT_COLUMN:
            try:
                used_index = self.get_item_index(self.cls.ImageSize)
                total_index = self.get_item_index(self.cls.Memory)
                used = record[used_index]
                total = record[total_index]
                return float(used/(total * 1024)) * 100.0
            except:
                return 0

        return super(DashboardCapacitySlotSummary, self).get_item_value(session, item)

    def get_item_unit(self, session, item):
        return item.unit

    def render_formatted_value(self, session, item, value, escape=False):
        if item is self.PERCENT_COLUMN:
            return "%0.02f%%" % value
        return super(DashboardCapacitySlotSummary, 
                     self).render_formatted_value(session, item, value, escape)

    def render_html_title(self, session, item):
        if item is self.PERCENT_COLUMN:
            return item
        return super(DashboardCapacitySlotSummary, self).render_html_title(session, item)

    def get_legend_class(self, session, item):
        return "blank"

class GridSlotsSummary(PieStatSet):
    def __init__(self, app, name, collector):
        super(GridSlotsSummary, self).__init__(app, name, collector, "collector.hosts")

        self.attrs = ["HostsClaimed", "HostsUnclaimed",
                      "HostsOwner", "HostsTotal"]

        self.has_total = True
        self.color_scheme = PieChartPage.BLUES

        self.chart_link = StatFlashChart(app, "popup", collector)
        self.chart_link.stats = list(reversed(self.attrs[:-1]))
        self.chart_link.chart_type = "stacked"
        self.chart_link.duration.param.default = "3600"
        self.add_child(self.chart_link)

    def render_title(self, session):
        return "Host info"

    def is_total(self, item):
        index = self.attrs.index(item[0].name)
        return index == len(self.attrs) - 1

    def get_legend_class(self, session, item):
        index = self.attrs.index(item[0].name)
        return "legend%s" % rgb_to_string(*(PieChartPage.color_schemes[self.color_scheme][index]))

    def render_html_title(self, session, item):
        index = self.attrs.index(item[0].name)
        return "Aggregate of %s for all slots" % self.attrs[index]

class DashboardOSData(ObjectSqlAdapter):
    def __init__(self, app):
        cls = app.model.com_redhat_grid.Slot
        super(DashboardOSData, self).__init__(app, cls)

        self.sum_column = "\"OpSys\""

        col = "count(%s)" % self.sum_column
        self.columns.append(self.sum_column)
        self.columns.append(col)

        self.act_state_column = AliasSqlColumn("\"Activity\"||\"State\"", "actstate")
        self.columns.append(self.act_state_column)

    def get_records(self, session):
        values = dict()

        options = SqlQueryOptions()
        options.sort_column = self.sum_column
        options.group_column = ",".join((self.sum_column, self.act_state_column.identifier))

        records = self.get_data(values, options)

        # accumulate records by os/used|unused manually
        recs_by_os = dict()
        for record in records:
            os, count, act_state = record
            if os not in recs_by_os:
                recs_by_os[os] = dict()
                recs_by_os[os]["total"] = 0
                recs_by_os[os]["used"] = 0
                recs_by_os[os]["unused"] = 0
            recs_by_os[os]["total"] += count
            if act_state == "IdleUnclaimed":
                recs_by_os[os]["unused"] += count
            else:
                recs_by_os[os]["used"] += count

        records = list()
        for os in sorted(recs_by_os.keys()):
            records.append(("%s used" % os, recs_by_os[os]["used"]))
            records.append(("%s unused" % os, recs_by_os[os]["unused"]))
            records.append(("%s total" % os, recs_by_os[os]["total"]))

        ########## dummy test data
        """
        records.append(("WINNT80 Used", 10))
        records.append(("WINNT80 Unused", 20))
        records.append(("WINNT80 Total", 30))
        records.append(("SOLARIS27 Used", 12))
        records.append(("SOLARIS27 Unused", 34))
        records.append(("SOLARIS27 Total", 46))
        """

        return records

    def get_sql_options(self, options):
        return options

    def get_id_field(self, cls):
        return None

class GridOSBreakdown(PieStatSet):
    def __init__(self, app, name):
        super(GridOSBreakdown, self).__init__(app, name, None, "slot.os")

        self.os_records = Attribute(app, "os_breakdown")
        self.add_attribute(self.os_records)

        self.os_data = DashboardOSData(app)

        self.color_scheme = PieChartPage.GROUP2
        self.has_total = True

    def get_records(self, session):
        os_records = self.os_records.get(session)
        if not os_records:
            os_records = self.os_data.get_records(session)
            self.os_records.set(session, os_records)
        return os_records

    def do_render(self, session):
        records = self.get_records(session)
        if len(records):
            return super(GridOSBreakdown, self).do_render(session)

    def render_title(self, session):
        return "Slot breakdown by OS"

    def do_get_items(self, session):
        # (index, (name, value))
        return [(i, x) for i, x in enumerate(self.get_records(session))]

    def is_total(self, item):
        _, record = item
        return "total" in record[0]

    def render_item_title(self, session, item):
        _, record = item
        return record[0]

    def get_item_value(self, session, item):
        _, record = item
        return record[1]

    def render_item_value(self, session, item):
        return xml_escape(self.get_item_value(session, item))

    def render_html_title(self, session, item):
        (_, (name, value)) = item
        os, _, state = rpartition(name, " ")
        return "There are %d %s slots with an OS of %s" % (value, state, os)

    def get_legend_class(self, session, this_item):
        items = self.do_get_items(session)
        real_index = 0
        for item in items:
            if item[1][0] is this_item[1][0]:
                break
            if not self.is_total(item):
                real_index += 1
        return "legend%s" % rgb_to_string(*(PieChartPage.color_schemes[self.color_scheme][real_index]))

class NegotiatorDefinitionStatSet(PieStatSet):
    def __init__(self, app, name, title):
        cls = app.model.com_redhat_grid.Negotiator
        self.negotiator = YoungestAttribute(app, "neg", cls)
        super(NegotiatorDefinitionStatSet, self).__init__(app, name, self.negotiator, title)
        self.add_attribute(self.negotiator)

        self.chart_link = StatFlashChart(app, "popup", self.negotiator)
        self.add_child(self.chart_link)

    def is_total(self, item):
        if not self.has_total:
            return False
        index = self.attrs.index(item[0].name)
        return index == len(self.attrs) - 1

    def get_legend_class(self, session, item):
        index = self.attrs.index(item[0].name)
        return "legend%s" % rgb_to_string(*(PieChartPage.color_schemes[self.color_scheme][index]))

class NegotiatorJobThroughput(Widget):
    def __init__(self, app, name):
        super(NegotiatorJobThroughput, self).__init__(app, name)

        self.attrs = ["NumJobsConsidered", "Matches", "CandidateSlots", "MatchRate"]

        throughput_stats = JobThroughput(app, "stats", self.attrs)
        self.add_child(throughput_stats)

        chart = self.ThroughputChart(app, "timeseries", throughput_stats.negotiator)
        chart.duration.param.default = "3600"
        chart.stats = self.attrs[:-1]
        self.add_child(chart)

    class ThroughputChart(StatFlashChart):
        def do_render(self, session):
            obj = self.object.get(session)
            if obj:
                return super(NegotiatorJobThroughput.ThroughputChart, self).do_render(session)

        def render_title(self, session):
            return "Recent negotiator job throughput"

class JobThroughput(NegotiatorDefinitionStatSet):
    def __init__(self, app, name, attrs):
        super(JobThroughput, self).__init__(app, name, "job.throughput")

        self.attrs = attrs

        self.remove_child(self.chart_link)
        self.chart_link = None

        self.has_total = False
        self.has_pie_chart = False

    def render_title(self, session):
        return "Current negotiator job throughput"

    def get_legend_class(self, session, item):
        return "blank"

    def render_html_title(self, session, item):
        return super(JobThroughput, self).render_html_title(session, item[0])

class MonitorSelfSchedulerTable(ObjectSelector):
    def __init__(self, app, name, cls, frame):
        super(MonitorSelfSchedulerTable, self).__init__(app, name, cls)

        col = ObjectLinkColumn(app, "name", cls.Name, cls._id, frame)
        self.add_column(col)

        stat = MonitorSelfAgeColumn(app, "monitorSelfAge", cls.MonitorSelfAge)
        self.add_column(stat)

        self.add_attribute_column(cls.JobSubmissionRate)
        self.add_attribute_column(cls.JobStartRate)
        self.add_attribute_column(cls.JobCompletionRate)

        stat = MonitorSelfStatColumn(app, cls.MonitorSelfCPUUsage.name, cls.MonitorSelfCPUUsage)
        self.add_column(stat)

        stat = MonitorSelfStatColumn(app, cls.MonitorSelfImageSize.name, cls.MonitorSelfImageSize)
        self.add_column(stat)

        self.enable_csv_export()

    def create_table(self, app, name, cls):
        # avoid the checkboxes
        return MinimalTable(app, name, cls)

class SchedulerPerformance(Widget):
    def __init__(self, app, name):
        super(SchedulerPerformance, self).__init__(app, name)

        cls = app.model.com_redhat_grid.Scheduler
        frame = "main.grid.scheduler"

        self.table = MonitorSelfSchedulerTable(app, "current", cls, frame)
        self.add_child(self.table)

        rates = WidgetSet(app, "rate_widgets")
        self.add_child(rates)

        others = WidgetSet(app, "other_widgets")
        self.add_child(others)

        cls = app.model.com_redhat_grid.Scheduler
        columns = (cls.JobsSubmitted, cls.JobSubmissionRate, cls.JobsSubmittedCum)
        stats = DashboardSummaryStats(app, "submitted", cls, columns, "Jobs.Submitted")
        stats.title = "Aggregate job submission stats"
        rates.add_child(stats)

        columns = (cls.JobsStarted, cls.JobStartRate, cls.JobsStartedCum)
        stats = DashboardSummaryStats(app, "started", cls, columns, "Jobs.Started")
        stats.title = "Aggregate job started stats"
        rates.add_child(stats)

        columns = (cls.JobsCompleted, cls.JobCompletionRate, cls.JobsCompletedCum)
        stats = DashboardSummaryStats(app, "completed", cls, columns, "Jobs.Completed")
        stats.title = "Aggregate job completion stats"
        rates.add_child(stats)

        columns = (cls.JobsExited, cls.JobsExitedCum)
        stats = DashboardSummaryStats(app, "exited", cls, columns, "Jobs.Exited")
        stats.title = "Aggregate job exited stats"
        others.add_child(stats)

        columns = (cls.ShadowExceptions, cls.ShadowExceptionsCum)
        stats = DashboardSummaryStats(app, "exceptions", cls, columns, "Jobs.Exceptions")
        stats.title = "Aggregate job shadow exceptions stats"
        others.add_child(stats)

        self.footnote_data = DashboardSumData(app, [cls.WindowedStatWidth.name], cls)

    def render_footnote_value(self, session):
        # get the average WindowedStarWidth for all schedulers
        data = self.footnote_data.get_record(session)
        try:
            value = data[0] / data[1]
        except:
            value = 0
        return value

    def render_title(self, session):
        return "Scheduler performance"

    def render_table(self, session):
        return self.table.render(session)

class MonitorSelfStats(Widget):
    def __init__(self, app, name, cls, title, frame, object):
        super(MonitorSelfStats, self).__init__(app, name)

        self.cls = cls
        self.frame = frame
        self.title = title
        self.object = object
        self.add_attribute(self.object)

        self.chart_link = MonitorSelfCharts(app, "history", self.object)
        self.add_child(self.chart_link)

        table = MonitorSelfTable(app, "current", cls, frame, True)
        self.add_child(table)

    def do_render(self, session):
        if self.object.get(session):
            return super(MonitorSelfStats, self).do_render(session)

    def render_title(self, session):
        return self.title

class MonitorSelfTable(ObjectSelector):
    def __init__(self, app, name, cls, frame, static):
        super(MonitorSelfTable, self).__init__(app, name, cls)

        # Do we want the name column to link to the objects page?
        # In the case of collector we don't
        if frame:
            col = ObjectLinkColumn(app, "name", cls.Name, cls._id, frame)
        else:
            col = ObjectTableColumn(app, cls.Name.name, cls.Name)
        col.static_header = static
        self.add_column(col)

        stat = MonitorSelfAgeColumn(app, "monitorSelfAge", cls.MonitorSelfAge)
        stat.static_header = static
        self.add_column(stat)
        
        stat = MonitorSelfStatColumn(app, cls.MonitorSelfRegisteredSocketCount.name, cls.MonitorSelfRegisteredSocketCount)
        stat.static_header = static
        self.add_column(stat)

        stat = MonitorSelfStatColumn(app, cls.MonitorSelfCPUUsage.name, cls.MonitorSelfCPUUsage)
        stat.static_header = static
        self.add_column(stat)

        stat = MonitorSelfStatColumn(app, cls.MonitorSelfImageSize.name, cls.MonitorSelfImageSize)
        stat.static_header = static
        self.add_column(stat)

        self.enable_csv_export()

    def create_table(self, app, name, cls):
        # avoid the checkboxes
        return MinimalTable(app, name, cls)

    def render_title(self, session):
        return "Current"

class MonitorSelfCharts(Widget):
    def __init__(self, app, name, object):
        super(MonitorSelfCharts, self).__init__(app, name)

        cpu = self.CPUFlashChart(app, "cpu", object)
        cpu.stats = ("MonitorSelfCPUUsage",)
        self.add_child(cpu)

        used = self.SocketFlashChart(app, "used", object)
        used.stats = ("MonitorSelfRegisteredSocketCount",)
        self.add_child(used)

    def render_title(self, session):
        return "History"

    class CPUFlashChart(StatFlashChart):
        def render_title(self, session, *args):
            return "CPU usage"

    class SocketFlashChart(StatFlashChart):
        def render_title(self, session, *args):
            return "Socket count"

