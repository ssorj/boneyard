import cStringIO
import logging
from datetime import datetime, timedelta
from time import time, sleep
import threading

from wooly import Widget, Page, Parameter, Attribute
from wooly.util import StringCatalog, escape_entity, Writer
from wooly.widgets import ItemSet
from wooly.pages import HtmlPage
from wooly.parameters import IntegerParameter, ListParameter, StringParameter,\
    BooleanParameter

from cumin.formats import fmt_bytes, fmt_duration_brief
from cumin.model import CuminStatistic, SamplesSqlAdapter
from cumin.widgets import StateSwitch
from wooly.template import WidgetTemplate
from cumin.util import calc_rate, secs, nvl, xml_escape
from cumin.OpenFlashChart import Element, Chart

from rosemary.sqlfilter import SqlFilter

strings = StringCatalog(__file__)
log = logging.getLogger("cumin.stat")

class StatSet(ItemSet):
    def __init__(self, app, name, object):
        super(StatSet, self).__init__(app, name)

        self.object = object
        self.attrs = list()
        self.update_enabled = True

    def get_fields(self, session):
        return self.attrs

    def do_get_items(self, session):
        object = None
        if self.object:
            object = self.object.get(session)
        if not object:
            return []

        stats = list()
        for field in self.get_fields(session):
            cls = object._class._statistics_by_name[field]
            stats.append((cls, getattr(object, cls.name, None)))
        return stats

    def render_item_title(self, session, item):
        stat, _ = item
        return stat.title

    def render_html_title(self, session, item):
        stat, _ = item
        return stat.description

    def render_item_value(self, session, item):
        value = self.get_item_value(session, item)
        return self.render_formatted_value(session, item, value, escape=True)

    def get_item_unit(self, session, item):
        stat, _ = item
        return stat.unit

    def get_item_value(self, session, item):
        _, value = item
        return value

    def render_formatted_value(self, session, item, value, escape=False):
        # Since this routine delegates to CuminStatistic which may produce
        # xml for None values, we need to handle escaping here and in
        # CuminStatistic
        def fmt_b(value):
            return value is not None and fmt_bytes(value) or None

        def fmt_kb(value):
            return value is not None and fmt_bytes(value * 1024) or None

        def fmt_mb(value):
            return value is not None and fmt_bytes(value * 1024 * 1024) or None

        try:
            format = self.get_item_unit(session, item)
            if format:
                if format == "MiB":
                    return fmt_mb(value)
                elif format == "KiB":
                    return fmt_kb(value)
        except:
            pass

        return CuminStatistic.fmt_value(value, escape)

class NewStatSet(ItemSet):
    def __init__(self, app, name):
        super(NewStatSet, self).__init__(app, name)

        self.stats = list()
        self.update_enabled = True

    def render_rate_text(self, session):
        return "Per second"

    def get_values(self, session):
        return list()

    def do_get_items(self, session):
        return zip(self.stats, self.get_values(session))

    def render_item_title(self, session, item):
        stat, _ = item
        return stat.get_title(session)

    def render_item_name(self, session, item):
        stat, _ = item
        return stat.name

    def render_item_value(self, session, item):
        stat, value = item
        return stat.format_value(session, value, escape=True)

class DurationSwitch(StateSwitch):
    def __init__(self, app, name):
        super(DurationSwitch, self).__init__(app, name)

        self.add_state("600", "10 minutes")
        self.add_state("3600", "1 hour")
        self.add_state("86400", "1 day")

class JSDurationSwitch(DurationSwitch):
    def get_click(self, session, state):
        return "return changeDuration('%s', this, '%s')" % (state, self.parent.path)

    def get_attributes(self, state):
        return {'state': state}

class StatValueChart(Widget):
    def __init__(self, app, name, object):
        super(StatValueChart, self).__init__(app, name)

        self.object = object

        self.mode = None
        self.stats = ()
        self.chart_type = None
        self.title = None

        self.stats_tmpl = WidgetTemplate(self, "stat_html")

        self.duration = JSDurationSwitch(app, "duration")
        self.add_child(self.duration)

        self.fullpageable = True

    def get_href_params(self, session):
        object = self.object.get(session)
        params = list()

        # Ask the object for a list of values that uniquely identifies it.
        # Signature is the name of a ListParameter that will hold the values
        # as an ordered list.  The values can be passed back to the class to
        # retrieve the object (or its samples)
        signature = object.get_signature()
        for s in signature:
            params.append("signature=%s" % s)

        params.append("chart_id=%s" % self.render_id(session, None))
        params.append("duration=%s" % self.duration.get(session))
        params.append("rpkg=%s" % object._class._package._name)
        params.append("rcls=%s" % object._class._name)

        for stat in self.stats:
            params.append("stat=%s" % stat)

        if self.mode:
            params.append("mode=%s" % self.mode)
            
        if self.chart_type:
            params.append("type=%s" % self.chart_type)
            
        return params

    def render_href(self, session):
        params = self.get_href_params(session)
        return escape_entity("%s?" % self.get_chart_name(session) + ";".join(params))

    def get_chart_name(self, session):
        return "stats.png"

    def render_fullpageable(self, session):
        return self.fullpageable and " fullpageable" or ""

    def render_title(self, session):
        if self.title:
            return self.title

        object = self.object.get(session)
        cls = object._class
        return getattr(cls, self.stats[0]).title

    def render_width(self, session):
        return 360

    def render_height(self, session):
        return 100

class ReportingStatValueChart(StatValueChart):
    def __init__(self, app, name, cls):
        super(ReportingStatValueChart, self).__init__(app, name, None)
        
        self.cls = cls
        self.duration.add_state("2592000", "1 month")
        self.duration.add_state("31557600", "1 year") 
        self.max_samples = 0
        self.filters = list()

    def get_href_params(self, session):
        params = list()

        params.append("chart_id=%s" % self.render_id(session, None))
        params.append("duration=%s" % self.duration.get(session))
        params.append("rpkg=%s" % self.cls._package._name)
        params.append("rcls=%s" % self.cls._name)
        params.append("type=%s" % "reportarea")
        
        for i, stat in enumerate(self.stats):
            params.append("stat=%s" % stat)

        if self.mode:
            params.append("mode=%s" % self.mode)
            
        params.append("maxsamp=%s" % self.max_samples)          

        return params

class StatStackedChart(StatValueChart):
    def __init__(self, app, name):
        super(StatStackedChart, self).__init__(app, name)

        self.duration = JSDurationSwitch(app, "duration")
        self.add_child(self.duration)

    def get_chart_name(self, session):
        return "stacked.png"

    def render_height(self, session):
        return 200

class StatFlashChart(StatValueChart):
    def get_flash_name(self, session):
        return "chart.json"

    def render_img_href(self, session):
        return super(StatFlashChart, self).render_href(session)

    def render_img_width(self, session):
        return super(StatFlashChart, self).render_width(session)

    def render_img_height(self, session):
        return super(StatFlashChart, self).render_height(session)

    def render_href(self, session):
        params = self.get_href_params(session)
        return escape_entity("%s?" % self.get_flash_name(session) + ";".join(params))

    def render_fullpage_href(self, session):
        params = self.get_href_params(session)
        return escape_entity("flashpage.html?" + ";".join(params))

    def render_width(self, session):
        return 360

    def render_height(self, session):
        return 120
    
    def render_id_nodots(self, session):
        return self.render_id(session).replace(".", "_")
    
class ReportingChart(ReportingStatValueChart):
    def get_flash_name(self, session):
        return "chart.json"

    def render_img_href(self, session):
        return super(ReportingChart, self).render_href(session)

    def render_img_width(self, session):
        return super(ReportingChart, self).render_width(session)

    def render_img_height(self, session):
        return super(ReportingChart, self).render_height(session)

    def render_href(self, session):
        params = self.get_href_params(session)
        return escape_entity("%s?" % self.get_flash_name(session) + ";".join(params))

    def render_fullpage_href(self, session):
        params = self.get_href_params(session)
        return escape_entity("flashpage.html?" + ";".join(params))

    def render_width(self, session):
        return 360

    def render_height(self, session):
        return 120
    
    def render_id_nodots(self, session):
        return self.render_id(session).replace(".", "_")   
    
    def render_filters(self, session):
        filtertext = ""
        for f in self.filters:
            filtertext += f.do_render(session)
            
        return filtertext
    
    class FilterInput(Widget):
        def __init__(self, app, name, cls, attr, param, title):
            super(ReportingChart.FilterInput, self).__init__(app, name)
            self.user_list = list()
            self.cls = cls
            self.attr = attr
            self.param = param
            self.title = title
            
        def render_onclick(self, session):
            return """onclick="updateFilter(this.getPrevious().value, this, '%s')" """ % self.parent.path

        def render_onchange(self, session):
            return """onchange="updateFilter(this.value, this, '%s', '%s')" """ % (self.parent.path, self.param)
        
        def render_name(self, session):
            return self.name
        
        def do_process(self, session):
            rows = self.cls.get_selection_samples(session.cursor)
            self.user_list = sorted(list(set((getattr(x, self.attr)) for x in rows)))

        def render_user_list(self, session):
            options = ""
            for u in self.user_list:
                options += """<option value="%s">%s</option>""" % (xml_escape(u), xml_escape(u))
                
            return options
        
        def render_title(self, session):
            return self.title
        
class ImageCache(object):
    def __init__(self):
        self.__files = dict() # {name: {"time": time_created, "file": file object, "cookie": (cookie values)}}

    def find_recent(self, name, max_age):
        if name in self.__files:
            age = timedelta(seconds=max_age)
            now = datetime.now()
            then = self.__files[name]["time"]
            if now - then < age:
                file = self.__files[name]["file"]
                file.seek(0)
                return (file.read(), self.__files[name]["cookie"])

        return (None, None)

    def get_current(self, name):
        if name in self.__files:
            file = self.__files[name]["file"]
            file.seek(0)
            return (file.read(), self.__files[name]["cookie"])
        else:
            return (None, None)


    def create_cache_file(self, name, args):
        if name not in self.__files:
            #file = tempfile.TemporaryFile()
            file = cStringIO.StringIO()
        else:
            file = self.__files[name]["file"]
            file.seek(0)
            file.truncate()

        self.__files[name] = {"time": datetime.now(), "file": file, "cookie": args}
        return file

class PieChartPage(Page):
    # handles pie.png request
    PAGE_NAME = "pie.png"
    RAINBOW = "rainbow"
    GREENS = "greens"
    BLUES = "blues"
    GROUP2 = "group2"
    BLANK = "blank"
    color_schemes = {"rainbow": [(0,0,1), (1,1,0), (1,0,1), (0,1,1), (1,0,0), (0,1,0)],
                     "greens":  [(0,1,0), (.9,1,.9), (.6,1,.6), (.3,.6,.3), (0,.5,0)],
                     "blues":   [(0,0,1), (.9,.9,1), (.6,.6,1), (.3,.3,.6), (0,0,.5)],
                     "group2":  [(0,0,1), (.6,.6,1),
                                (1,0,1), (1,.6,1),
                                (0,1,1), (.6,1,1),
                                (1,0,0), (1,.6,.6),
                                (.6,.6,0), (.3,.3,0),
                                (0,1,0), (.6,1,.6)],
                     "blank":   [(1,1,1), (1,1,1), (1,1,1), (1,1,1)]}

    def __init__(self, app, name):
        super(PieChartPage, self).__init__(app, name)

        param = IntegerParameter(app, "param")
        self.slices = ListParameter(app, "slice", param)
        self.add_parameter(self.slices)

        self.color_scheme = Parameter(app, "cs")
        self.add_parameter(self.color_scheme)

        self.radius = IntegerParameter(app, "r")
        self.add_parameter(self.radius)

    # used to keep all the parameter names and the page name in one class
    @classmethod
    def get_href(cls, items, scheme, radius):
        page = cls.PAGE_NAME

        tokens = ["slice=%d" % x for x in items]

        tokens.append("r=%s" % radius)

        assert scheme in cls.color_schemes.keys()
        tokens.append("cs=%s" % scheme)

        src = "%s?%s" % (page, ";".join(tokens))
        return src


    def get_content_type(self, session):
        return "image/png"

class StatChartPage(Page):
    # handles stats.png request
    def __init__(self, app, name):
        super(StatChartPage, self).__init__(app, name)

        self.rosemary_class = Parameter(app, "rcls")
        self.add_parameter(self.rosemary_class)

        self.rosemary_package = Parameter(app, "rpkg")
        self.add_parameter(self.rosemary_package)

        param = StringParameter(app, "sigparam")
        self.object_signature = ListParameter(app, "signature", param)
        self.add_parameter(self.object_signature)

        param = Parameter(app, "param")
        self.stats = ListParameter(app, "stat", param)
        self.add_parameter(self.stats)

        self.mode = Parameter(app, "mode")
        self.add_parameter(self.mode)

        # In seconds
        self.duration = IntegerParameter(app, "duration")
        self.duration.default = 600
        self.add_parameter(self.duration)

        self.interval = IntegerParameter(app, "interval")
        self.interval.default = -1
        self.add_parameter(self.interval)

        self.method = Parameter(app, "method")
        self.method.default = "avg"
        self.add_parameter(self.method)

        self.samples = BooleanParameter(app, "samples")
        self.add_parameter(self.samples)

        self.container_width = IntegerParameter(app, "width")
        self.container_width.default = 360
        self.add_parameter(self.container_width)

        self.container_height = IntegerParameter(app, "height")
        self.container_height.default = 100
        self.add_parameter(self.container_height)

        self.total_property = Parameter(app, "tp")
        self.add_parameter(self.total_property)

        self.type = Parameter(app, "type")
        self.add_parameter(self.type)
        
        self.maxsamp = IntegerParameter(app, "maxsamp")
        self.maxsamp.default = 0
        self.add_parameter(self.maxsamp)

        self.cache = ImageCache()

    def get_content_type(self, session):
        return self.samples.get(session) and "text/plain" or "image/png"

    def get_object_property(self, session, property):
        rpackage = self.rosemary_package.get(session)
        rclass = self.rosemary_class.get(session)
        signature = self.object_signature.get(session)

        rosemary_package = self.app.model._packages_by_name[rpackage]
        cls = rosemary_package._classes_by_name[rclass]
        cursor = self.app.database.get_read_cursor()
        object = cls.get_object_by_signature(cursor, signature)

        return object.get_value(property)

    def get_adapter_stats(self, session):
        rpackage = self.rosemary_package.get(session)
        rclass = self.rosemary_class.get(session)
        rosemary_package = self.app.model._packages_by_name[rpackage]
        rosemary_class = rosemary_package._classes_by_name[rclass]

        signature = self.object_signature.get(session)
        
        stats = [getattr(rosemary_class, x) for x in self.stats.get(session)]
        adapters = dict()
        for stat in stats:
            filters = list()
            if self.user_selection.get(session) is not None and self.user_selection.get(session).lower() != "<none>" and self.user_selection.get(session) != "": 
                filters.append(self.UserFilter(rosemary_class, self.user_selection.get(session)))
            if self.group_selection.get(session) is not None and self.group_selection.get(session).lower() != "<none>" and self.group_selection.get(session) != "": 
                filters.append(self.UserFilter(rosemary_class, self.group_selection.get(session)))
            adapters[stat] = SamplesSqlAdapter(self.app, rosemary_class, signature, session, filters)
            
            
        return (adapters, stats)
    
    class UserFilter(SqlFilter):
        def __init__(self, cls, value):
    
            table = cls.sql_samples_table
    
            fmt = "(%s like '%s')"
            args = (table.user.identifier, value)
    
            self.text = fmt % args
    
        def emit(self):
            return self.text
    # builds an object that is similar to a RosemaryStatistic that can 
    # be used later in the chart rendering to give values to the chart items
    class Pseudostat(object):
        def __init__(self, statname):
            name, title = statname.split('|')
            self.name = name
            self.title = title
            self.short_title = None

    def get_cache_control(self, session):
        return "no-cache"

    def gen_filename(self, session):
        return session.marshal()

    def get_cached(self, session, recent):
        filename = self.gen_filename(session)
        chart, args = self.cache.find_recent(filename, 30)
        if args:
            last_recent, samples, xy = args
            if recent == last_recent:
                return chart

    def get_cached_samples(self, session, recent):
        branch = session.branch()
        self.samples.set(branch, False)
        filename = self.gen_filename(branch)
        chart, args = self.cache.get_current(filename)
        if args:
            return (args['samples'], args['title_xy'])

    def cache_it(self, session, chart, args):
        filename = self.gen_filename(session)
        writer = self.cache.create_cache_file(filename, args)
        chart.write(writer)

    def get_interval(self, session, duration, width):
        interval = self.interval.get(session)
        if interval != -1:
            return interval
        else:
            max_samples = int(width * 1.5)
            return max(int(duration / max_samples), 1)

    def render_samples(self, session, recent):
        c = {(1,0,0): "red", (0,0,1): "blue", (0,1,0): "green"}
        cached_samples, title_xy = self.get_cached_samples(session, recent)
        if cached_samples:
            rets = dict()
            for stat in cached_samples:
                ret = dict()
                ret["color"] = c[cached_samples[stat][1]]
                ret["points"] = cached_samples[stat][0]
                ret["xy"] = title_xy[cached_samples[stat][1]]
                rets[stat.name] = ret
            return str(rets)
        
class ModifiedAgentIdParameter(StringParameter):
    def get(self, session):
        agent = super(ModifiedAgentIdParameter, self).get(session)
        return agent.replace("|", ":")

class FlashFullPage(HtmlPage):
    def __init__(self, app, name):
        super(FlashFullPage, self).__init__(app, name)

        self.updater = Widget(app, "updater")
        self.updater.update_enabled = True
        self.add_child(self.updater)

        param = StringParameter(app, "sigparam")
        self.object_signature = ListParameter(app, "signature", param)
        self.add_parameter(self.object_signature)

        self.rosemary_class = Parameter(app, "rcls")
        self.add_parameter(self.rosemary_class)

        self.rosemary_package = Parameter(app, "rpkg")
        self.add_parameter(self.rosemary_package)

        self.object = self.ObjectAttribute(app, "object")
        self.add_attribute(self.object)

        param = Parameter(app, "param")
        self.stats = ListParameter(app, "stat", param)
        self.add_parameter(self.stats)

        self.container_width = IntegerParameter(app, "width")
        self.container_width.default = 360
        self.add_parameter(self.container_width)

        self.container_height = IntegerParameter(app, "height")
        self.container_height.default = 100
        self.add_parameter(self.container_height)

        self.mode = Parameter(app, "mode")
        self.add_parameter(self.mode)

        self.chart_type = Parameter(app, "type")
        self.add_parameter(self.chart_type)

        self.flash_chart = self.GenericChart(app, "chart", self.object)
        self.add_child(self.flash_chart)

        self.total_property = Parameter(app, "tp")
        self.add_parameter(self.total_property)

    def render_content(self, session):
        self.flash_chart.stats = self.stats.get(session)
        self.flash_chart.mode = self.mode.get(session)
        self.flash_chart.chart_type = self.chart_type.get(session)
        return self.flash_chart.render(session)

    class ObjectAttribute(Attribute):
        def get(self, session):
            obj = super(FlashFullPage.ObjectAttribute, self).get(session)
            if not obj:
                rpackage = self.widget.rosemary_package.get(session)
                rclass = self.widget.rosemary_class.get(session)
                signature = self.widget.object_signature.get(session)
                rosemary_package = self.app.model._packages_by_name[rpackage]
                rosemary_class = rosemary_package._classes_by_name[rclass]

                cursor = self.app.database.get_read_cursor()
                obj = rosemary_class.get_object_by_signature(cursor, signature)

                self.set(session, obj)

            return obj

    class GenericChart(StatFlashChart):
        def render_width(self, session):
            return self.parent.container_width.get(session)

        def render_height(self, session):
            return self.parent.container_height.get(session)

        def render_img_href(self, session):
            params = self.get_href_params(session)
            params.append("width=%i" % self.render_width(session))
            params.append("height=%i" % self.render_height(session))
            return escape_entity("%s?" % self.get_chart_name(session) + ";".join(params))

        def render_href(self, session):
            params = self.get_href_params(session)
            params.append("width=%i" % self.render_width(session))
            params.append("height=%i" % self.render_height(session))
            params.append("high=1")
            tp = self.parent.total_property.get(session)
            if tp:
                params.append("tp=%s" % tp)
            return escape_entity("%s?" % self.get_flash_name(session) + ";".join(params))

class XAxis(object):
    def get_x_labels(self, duration, intervals, step, end_secs):
        x_step = float(duration) / float(intervals)
        labels = list()
        for i in range(0, intervals + 1):
            label = dict()
            if i % step == 0:
                value = int(round(duration - i * x_step + end_secs))
                text = fmt_duration_brief(value)

                label["text"] = text
            else:
                label["text"] = ""
            label["x"] = i * x_step

            labels.append(label)
        return labels

    def get_x_axis(self, duration, end_secs, tick_height=0):
        x_intervals = 8
        x_steps = 2
        if duration == 600:
            x_intervals = 10

        x_axis = Element()
        x_axis.colour = "#CCCCCC"
        x_axis.grid_colour = "#DDDDDD"
        x_axis.stroke = 1
        x_axis.tick_height = tick_height

        xlbls = Element()
        xlbls.size = 12
        xlbls.colour = "#999999"
        xlbls.align = "auto"
        xlbls.rotate = 0.0001

        lbls = self.get_x_labels(duration, x_intervals, x_steps, end_secs)
        xlbls.labels = lbls
        x_axis.labels = xlbls
        return x_axis

class FlashPieChart(Widget):
    colors = ['#FF0000', '#0000FF', '#00FF00', '#00FFFF', '#FF00FF', '#000000', '#666600']
    def __init__(self, app, name, page):
        super(FlashPieChart, self).__init__(app, name)
        self.page = page

    def create(self, session, adapter, stats):
        names = self.page.names.get(session)
        values = self.page.values.get(session)
        nvs = dict()
        for name, value in zip(names, values):
            nvs[name] = value

        # move Unclaimed to end of list
        sorted_names = sorted(names)
        sorted_names.remove("Unclaimed")
        sorted_names.append("Unclaimed")

        chart = Chart()
        chart.title.text = ""
        chart.bg_colour = "#FFFFFF"

        chart.elements = list()
        element = Element()
        element.type = "pie"
        element.alpha = 7
        element.start_angle = 0
        element.gradient_fill = True
        element.radius = 90

        element.animate = list()
        animation = Element()
        animation.type = "fade"
        element.animate.append(animation)
        animation = Element()
        animation.type = "bounce"
        animation.distance = 8
        element.animate.append(animation)
        element.tip = "#percent#"

        element.colours = []
        for i in range(len(sorted_names)):
            j = i % len(self.colors)
            if sorted_names[i] == "Unclaimed":
                color = "#EEEEEE"
            else:
                color = self.colors[j]
            element.colours.append(color)
        element.colours.append("#EEEEEE")

        element.on_click = "ofc_change_priority"
        id = self.page.chart_id.get(session)
        element.on_click_text = "#percent#|#val#|#label#|%s" % id

        element.values = [{"label": x, "value": float(nvs[x])} for x in sorted_names]

        chart.elements.append(element)
        return chart.create()

class FlashLineChart(Widget):
    colors = ('#FF0000', '#0000FF', '#00FF00', '#FF00FF', '#FFFF00', '#00FFFF', '#000000')
    one_day = 24 * 60 * 60
    def __init__(self, app, name, page):
        super(FlashLineChart, self).__init__(app, name)
        self.page = page

    def pos_to_seconds(self, pos):
        """ convert the flash chart slider position into a number of seconds ago """

        return int(round((1.0 - float(pos)) * self.one_day))

    def get_end_seconds(self, session):
        """ how many seconds ago the chart time span ends """

        cmax = self.page.control_max.get(session)
        if cmax:
            end_seconds_ago = self.pos_to_seconds(cmax)
        else:
            end_seconds_ago = 0
        return end_seconds_ago

    def get_time_span(self, session):
        """ the number of seconds between the chart begin and end """

        cmax = self.page.control_max.get(session)
        if cmax:
            cmin = self.page.control_min.get(session)
            start_seconds_ago = self.pos_to_seconds(cmin)
            end_seconds_ago = self.pos_to_seconds(cmax)
            return start_seconds_ago - end_seconds_ago
        else:
            return self.page.duration.get(session)

    def get_elapsed(self, session):
        """ load the javascript milliseconds since last update into a dict """

        elapsed = {'seconds': 0, 'milliseconds': 0.0, 'value': 0.0}
        e = self.page.elapsed.get(session)
        if e:
            js_milliseconds = long(e)
            seconds = int(js_milliseconds / 1000)
            milliseconds  = (js_milliseconds % 1000.0) / 1000.0
            elapsed['seconds'] = seconds
            elapsed['milliseconds'] = milliseconds
            elapsed['value'] = seconds + milliseconds
        return elapsed

    def get_duration(self, session):
        """ the number of seconds we want to get a sample for """

        duration = self.page.duration.get(session)
        e = self.page.elapsed.get(session)
        if e:
            elapsed = self.get_elapsed(session)
            if elapsed['seconds'] <= self.one_day:
                # allow some overlap so we don't drop samples
                duration = elapsed['seconds'] + 3
        else:
            duration = self.get_time_span(session)
        return duration

    def get_delta(self, session):
        """ if we get an elapsed parameter, we want
            to send only the new values, that is
            unless the elapsed value is too large
            in which case we want to get the entire sample """

        e = self.page.elapsed.get(session)
        if e:
            elapsed = self.get_elapsed(session)
            if elapsed['seconds'] <= self.one_day:
                return True
        return False

    def fix_method(self, method, mode):
        #if mode == "rate":
        #    return None
        return method

    def create(self, session, adapter, stats):
        # get the page parameters
        width = self.page.container_width.get(session)
        height = self.page.container_height.get(session)
        mode = self.page.mode.get(session)
        method = self.page.method.get(session)

        time_span = self.get_time_span(session)
        duration = self.get_duration(session)
        end_seconds_ago = self.get_end_seconds(session)
        delta = self.get_delta(session)

        interval = self.page.get_interval(session, duration, width)

        msg = "Chart parameters: duration: %s  end_secends_ago: %s  interval: %s" % (str(duration), str(end_seconds_ago), str(interval))
        log.debug(msg)
        # get the most recent samples
        samples = self.fetch_samples(adapter, duration, interval,
                                    self.fix_method(method, mode),
                                    mode, delta, stats,
                                    end_seconds_ago=end_seconds_ago)
        max_value, min_value = self.get_max_min(session, stats, samples, time_span, end_seconds_ago)

        append = False
        # if we should append the new samples, see if the y-axis has changed
        if delta:
            axis_max = self.page.axis_max.get(session)
            vals_max = self.page.vals_max.get(session)
            axis_for_vals = round(float(vals_max) * 1.1 + 1)
            max_of_axiis = max(max_value, axis_for_vals)
            # the most recent value(s) changed the y-axis range
            if axis_max != max_of_axiis:
                msg = "Y-Axis changed. New chart parameters: time_span: %s  end_secends_ago: %s  interval: %s" % (str(time_span), str(end_seconds_ago), str(interval))
                log.debug(msg)
                samples = self.fetch_samples(adapter, time_span, interval,
                                             self.fix_method(method, mode),
                                             mode, False, stats,
                                             end_seconds_ago=end_seconds_ago)
                max_value, min_value = self.get_max_min(session, stats, samples, time_span, end_seconds_ago)
            else:
                append = True

        #for sample, stat in zip(samples, stats):
        #    log.debug("samples in %s: %d" % (stat.name, len(samples[sample])))

        # create the chart dict
        chart = self.get_chart(session, adapter, stats, samples, time_span, max_value, min_value, append, end_seconds_ago)
        #print "**********\n"+chart.create()
        chart.graph_div = "%s_chart" % chart.id.replace(".", "_")
        return chart.create()

    def get_y_labels(self, absy, intervals, step):
        y_step = absy / intervals
        labels = list()
        for i in range(0, int(intervals) + 1):
            label = dict()

            if i % step == 0:
                value = int(round(i * y_step, 0))

                if value >= 1000000:
                    svalue = "%.2fM" % (round(value / 1000000.0, 2))
                elif value >= 10000:
                    svalue = "%ik" % int(round(value / 1000.0, -1))
                else:
                    svalue = str(value)

                label["text"] = svalue
                label["y"] = int(i * y_step)
                labels.append(label)

        return labels

    def get_y_axis(self, max_value, min_value):
        absy = max_value - min_value
        y_intervals = min(6, absy)

        y_steps = int(absy / y_intervals)
        y_label_steps = 2
        if absy <= 2:
            y_label_steps = 1

        #if int(max_value) < 3:
        #    y_steps = 3

        # .swf won't show grid lines without a y_axis on the left
        y_axis = {
            "min": int(min_value),
            "max": int(max_value),
            "steps": y_steps,
            "stroke": 1,
            "tick-length": 0,
            "colour": "#CCCCCC",
            "grid-colour": "#DDDDDD",
            "labels": {"labels": []}}
        y_axis_right = {
            "min": int(min_value),
            "max": int(max_value),
            "tick-length": 0,
            "stroke": 1,
            "colour": "#BBBBBB",
            "labels": {"colour": "#AAAAAA", "labels": self.get_y_labels(absy, y_intervals, y_label_steps)}}

        return y_axis, y_axis_right

    def fetch_samples(self, adapter, dur, interval, method, mode, delta, stats, end_seconds_ago=0):
        return dict()

    def get_max_min(self, session, stats, samples):
        return 0, 0

    def get_chart(self, session, adapter, stats, samples, duration, max_value, min_value, append, end_secs):
        return Chart()

class AreaChart(FlashLineChart):
    def __init__(self, app, name, page):
        super(AreaChart, self).__init__(app, name, page)

        self.alpha = 3
    
    def getStatSamples(self, adapter, samples, stat, dur, interval, method, end_seconds_ago, delta):
        # get more samples than needed to allow chart to clip correctly (explains the + 600)
        samples[stat] = adapter[stat].samples(stat, dur+600, interval, method, secs2=end_seconds_ago, delta=delta)
    
    def fetch_samples(self, adapter, dur, interval, method, mode, delta, stats, end_seconds_ago=0):
        samples = dict()
        if mode == "rate":
            for stat in stats:
                os = adapter.samples(stat, dur+600, interval, method, secs2=end_seconds_ago, delta=delta)
                ns = list()
                prev = None

                for sample in reversed(os):
                    if prev is not None:
                        rate = calc_rate(float(sample[1]), float(prev[1]),
                                         secs(sample[0]), secs(prev[0]))

                        ns.insert(0, (sample[0], rate, None))

                    prev = sample

                samples[stat] = ns
        else:
            threads = []
            for i, stat in enumerate(stats):
                # start a thread to do the db query, etc for each stat requested
                threads.append(threading.Thread(target = self.getStatSamples, args = (adapter, samples, stat, dur, interval, method, end_seconds_ago, delta)))
                threads[i].start()

        for th in threads:
            while th.isAlive():
                pass
                
        return samples

    def get_max_min(self, session, stats, samples, time_span=99999, end_seconds_ago=0):
        # take stddev into account for max and min y values
        max_value = 0
        min_value = 0

        for stat in stats:
            for x in samples[stat]:
                try:
                    #  Only compute the y-axis based on visible data
                    #  be sure to factor-in end_seconds_ago and time_span
                    time_change =  timedelta(seconds=end_seconds_ago)
                    window_adjusted_time = datetime.now() - time_change
                    if( (window_adjusted_time - x[0]).seconds <= int(time_span)):
                        devmax = nvl(x[1], 0) + float(nvl(x[2], 0))
                        devmin = nvl(x[1], 0) - float(nvl(x[2], 0))
                        max_value = max(max_value, devmax)
                        min_value = min(min_value, devmin)
                except Exception, err:
                    log.debug(err)


        max_value = round(max_value * 1.1 + 1)
        if min_value < 0:
            min_value = round(min_value * 1.1 - 1)

        return max_value, min_value

    def get_vals(self, session, samples, stat, text, duration, end_secs):
        tnow = time()
        vals = list()

        min_dt = tnow - duration - end_secs
        for dt, value, dev in samples[stat]:
            if value is not None:
                vals.append({"dt": secs(dt), "y": value})
                if secs(dt) < min_dt:
                    break

        vals.sort(key=lambda stat: stat["dt"], reverse=False) #here, we sort by dt to be sure that our graphs are valid
        return vals

    def make_chart_lines(self, session, chart, line_type, stats, dot_size, halo_size, line_width, samples, duration, end_secs, mode):
        chart.elements = list()
        for stat, color in reversed(zip(stats, self.colors)):
            line = Element()
            line.type = line_type
            line.fill = color
            line.fill_alpha = self.alpha
            line.on_show.type = "No"

            line.dot_style = {"type": "solid-dot",
                              "dot-size": dot_size,
                              "halo-size": halo_size}
            line.colour = color
            line.width = line_width
            tip_title = stat.title.split(" ")[-1]
            line.text = mode == "rate" and "%s / sec" % tip_title or self.get_line_title(stat)

            vals = self.get_vals(session, samples, stat, line.text, duration, end_secs)
            line.values = vals
            chart.elements.append(line)

    def get_line_title(self, stat):
        return stat.short_title and stat.short_title or stat.title
        return stat.title

    def get_chart(self, session, adapter, stats, samples, duration, max_value, min_value, append, end_secs):
        mode = self.page.mode.get(session)

        width = self.page.container_width.get(session)
        dot_size = 1
        halo_size = 0
        line_width = 0
        if width > 400:
            dot_size = 3
            halo_size = 1

        chart = Chart()
        id = self.page.chart_id.get(session)
        if isinstance(id, unicode):
            id = id.encode('ascii', 'replace')
        chart.id = id
        chart.bg_colour = "#FFFFFF"
        chart.tnow =  time()
        chart.duration = duration
        chart.end_secs = end_secs

        self.make_chart_lines(session, chart, "area", stats, dot_size, halo_size, line_width, samples, duration, end_secs, mode)

        if append:
            chart.append = self.get_elapsed(session)['value']
            return chart

        chart.title.text = ""
        chart.title.style = "{text-align: left; font-weight: bold; font-size: 14px;}"
        chart.tooltip = {"colour": "#000033",
                         "background": "#FFFFCC",
                         "stroke": 1,
                         "title": "{background-color: #000022; color: #FFFFFF; font-size: 1em;}",
                         "body": "{font-size: 10px; color: #000000;}"
                         }

        chart.x_axis = XAxis().get_x_axis(duration, end_secs)
        y_axis, y_axis_right = self.get_y_axis(max_value, min_value)
        chart.y_axis = y_axis
        chart.y_axis_right = y_axis_right

        # if we are big enough, add a control slider to pan and zoom
        if width > 400:
            chart.control.bg_colour = "#DDDDDD"
            chart.control.x_axis = XAxis().get_x_axis(self.one_day, 0, tick_height=10)
            chart.control.x_axis.labels.colour = "#333333"
            chart.control.x_axis.grid_colour = "#FFFFFF"
            samples = self.fetch_samples(adapter, self.one_day, 180, "avg", mode, False, stats, end_seconds_ago=0)
            self.add_control_points(session, stats, samples)
            max_value, min_value = self.get_max_min(session, stats, samples)
            self.make_chart_lines(session, chart.control, "area", stats, 1, 0, 0, samples, self.one_day, 0, mode)
            chart.control.y_min = max(min_value, 0)
            chart.control.y_max = max(max_value-2, 1)
            chart.control.slider_low.value = float(self.page.control_min.get(session))
            chart.control.slider_low.colour = "#666666"
            chart.control.slider_high.value = float(self.page.control_max.get(session))
            chart.control.slider_high.colour = "#666666"
            chart.control.tnow =  time()
            chart.control.duration = self.one_day
            chart.control.end_secs = 0

        #print "sending entire sample set with y_axis.max=%i" % chart.y_axis["max"]
        return chart

    def add_control_points(self, session, stats, samples):
        new_samples = list()
        threshold = timedelta(minutes=10)
        for stat in stats:
            last_dt = None
            last_val = 0
            for dt, value, dev in samples[stat]:
                if last_dt and last_dt - dt > threshold:
                    if last_val:
                        new_samples.append((last_dt, 0, 0))
                    if value:
                        new_samples.append((dt, 0, 0))
                last_dt = dt
                last_val = value
                new_samples.append((dt, value, dev))
            samples[stat] = new_samples
            
class ReportAreaChart(AreaChart):
    pass            

class StackedAreaChart(AreaChart):
    colors = ('#FFABAB', '#ABABFF', '#ABFFAB', '#FFABFF', '#FFFFAB', '#ABFFFF', '#ABABAB')
    def __init__(self, app, name, page):
        super(StackedAreaChart, self).__init__(app, name, page)

        self.points = self.Points(app, "points")
        self.add_attribute(self.points)

        self.alpha = 1

    def get_max_min(self, session, stats, samples, time_span, end_seconds_ago):
        max_value = 0
        min_value = 0
        points = dict()
        totals = dict()
        collapsed = dict()

        for stat in stats:
            last_dt = None
            for dt, value, dev in samples[stat]:
                if value == None:
                    value = 0
                if stat not in points:
                    points[stat] = list()
                if dt not in totals:
                    totals[dt] = 0

                if dt == last_dt:
                    if (totals[dt] > 0) and value > 0:
                        continue
                    points[stat].append((dt, 0, 0))
                else:
                    last_dt = dt
                    totals[dt] += value

                    points[stat].append((dt, value, totals[dt]))

                    max_value = max(totals[dt], max_value)
                    min_value = min(totals[dt], min_value)


        # save the accumulated values for each timestamp
        self.points.set(session, points)

        max_value = round(max_value * 1.1 + 1)
        if min_value < 0:
            min_value = round(min_value * 1.1 - 1)

        return max_value, min_value

    def get_vals(self, session, samples, stat, text, duration, end_secs):
        tnow = time()
        vals = list()
        points = self.points.get(session)

        if points:
            min_dt = tnow - duration - end_secs
            for dt, value, stacked_value in points[stat]:
                if value is not None:
                    vals.append({"dt": secs(dt), "y": stacked_value})
                    if secs(dt) < min_dt:
                        break

        vals.reverse()
        return vals

    class Points(Attribute):
        def get_default(self, session):
            return dict()

class StatFlashPage(StatChartPage):
    # handles chart.json requests
    def __init__(self, app, name):
        super(StatFlashPage, self).__init__(app, name)

        # number of milliseconds since the last update
        self.elapsed = Parameter(app, "elapsed")
        self.elapsed.default = None
        self.add_parameter(self.elapsed)

        # the current y-axis max reported by the .swf
        self.axis_max = IntegerParameter(app, "amax")
        self.axis_max.default = 0;
        self.add_parameter(self.axis_max)

        # the max y value reported by the .swf
        self.vals_max = IntegerParameter(app, "vmax")
        self.vals_max.default = 0;
        self.add_parameter(self.vals_max)

        self.chart_type = Parameter(app, "type")
        self.chart_type.default = "area"
        self.add_parameter(self.chart_type)

        self.chart_id = Parameter(app, "chart_id")
        self.add_parameter(self.chart_id)

        self.action = Parameter(app, "action")
        self.add_parameter(self.action)

        name = Parameter(app, "n")
        self.add_parameter(name)

        self.names = ListParameter(app, "name", name)
        self.add_parameter(self.names)

        val = Parameter(app, "v")
        self.add_parameter(val)

        self.values = ListParameter(app, "value", val)
        self.add_parameter(self.values)

        self.control_min = Parameter(app, "low")
        ten_min_of_day = 10.0 / (24.0 * 60.0)
        one_hour = 1 / 24.0
        self.control_min.default = str(1.0 - one_hour)
        self.add_parameter(self.control_min)

        self.control_max = Parameter(app, "high")
        self.control_max.default = None
        self.add_parameter(self.control_max)

        self.percent_property = Parameter(app, "tp")
        self.add_parameter(self.percent_property)
        
        self.user_selection = Parameter(app, "userc")
        self.user_selection.default = None
        self.add_parameter(self.user_selection)
        
        self.group_selection = Parameter(app, "groupc")
        self.group_selection.default = None
        self.add_parameter(self.group_selection)

    def get_content_type(self, session):
        return "text/plain"

    def do_render(self, session):
        adapter, stats = self.get_adapter_stats(session)

        chart = self.chart_factory(self.chart_type.get(session))
        return chart.create(session, adapter, stats)

    def chart_factory(self, chart_type):
        if chart_type == "area":
            chart_obj = AreaChart(self.app, chart_type, self)
        elif chart_type == "stacked":
            chart_obj = StackedAreaChart(self.app, chart_type, self)
            #chart_obj = StackedChart(self.app, chart_type, self)
        elif chart_type == "percent":
            chart_obj = PercentAreaChart(self.app, chart_type, self)
        elif chart_type == "pie":
            chart_obj = FlashPieChart(self.app, chart_type, self)
        elif chart_type == "reportarea":
            chart_obj = ReportAreaChart(self.app, chart_type, self)            
            

        return chart_obj

class PercentAreaChart(AreaChart):
    def get_max_min(self, session, stats, samples, time_span, end_seconds_ago):
        max_val, min_val = super(PercentAreaChart, self).get_max_min(session, stats, samples, time_span, end_seconds_ago)

        percent = self.page.percent_property.get(session)
        total = self.page.get_object_property(session, percent)
        total = total and float(total) or 1.0

        max_val = (max_val / total) * 100.0
        min_val = (min_val / total) * 100.0

        max_val = round(max_val * 1.1 + 1)
        # cap at 100
        max_val = min(max_val, 100.0)

        if min_val < 0:
            min_val = round(min_val * 1.1 - 1)

        return max_val, min_val

    def get_vals(self, session, samples, stat, text, duration, end_secs):
        tnow = time()
        vals = list()
        percent = self.page.percent_property.get(session)
        total = self.page.get_object_property(session, percent)

        min_dt = tnow - duration - end_secs
        for dt, value, dev in samples[stat]:
            if value is not None:
                if total is None or total == 0.0:
                    vals.append({"dt": secs(dt), "y": 0.0})
                else:
                    vals.append({"dt": secs(dt), "y": (float(value) / float(total)) * 100.0})
                if secs(dt) < min_dt:
                    break

        vals.reverse()
        return vals

    def get_line_title(self, stat):
        return "Percent %s" % stat.title

