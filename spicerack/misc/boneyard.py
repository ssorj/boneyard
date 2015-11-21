class ServerBrowser(Widget):
    def __init__(self, app, name):
        super(ServerBrowser, self).__init__(app, name)
        
        self.param = ServerGroupParameter(app, "group")
        self.add_parameter(self.param)

        self.groups = self.BrowserGroups(app, "groups")
        self.add_child(self.groups)

        self.servers = self.BrowserServers(app, "servers")
        self.add_child(self.servers)

    def get_args(self, session):
        return self.frame.get_args(session)

    def get_object(self, session):
        return self.param.get(session)

    def set_object(self, session, group):
        return self.param.set(session, group)

    def render_title(self, session, group):
        return "Servers %s" % fmt_count(len(self.app.model.get_servers()))

    def render_all_servers_link(self, session, group):
        class_ = group is None and "selected"

        branch = session.branch()
        self.set_object(branch, None)
        return link(branch.marshal(), "All Servers", class_)

    def render_add_group_href(self, session, group):
        branch = session.branch()
        self.page.show_server_group_add(branch)
        return branch.marshal()

    def render_edit_group_href(self, session, group):
        if group:
            branch = session.branch()
            self.page.show_server_group_edit(branch, group)
            return branch.marshal()

    def render_remove_group_href(self, session, group):
        if group:
            branch = session.branch()
            return branch.marshal()

    def render_groups(self, session, group):
        return self.groups.render(session, self.app.model)

    class BrowserGroups(Widget):
        def __init__(self, app, name):
            super(ServerBrowser.BrowserGroups, self).__init__(app, name)

            self.type_tmpl = WidgetTemplate(self, "type_html")
            self.group_tmpl = WidgetTemplate(self, "group_html")

        def get_items(self, session, model):
            return sorted_by(model.get_server_group_types())

        def render_types(self, session, model):
            writer = Writer()

            for type in self.get_items(session, model):
                self.type_tmpl.render(writer, session, type)

            return writer.to_string()

        def render_type_name(self, session, type):
            return type.name

        def render_groups(self, session, type):
            writer = Writer()
            
            for group in sorted_by(type.server_group_items()):
                self.group_tmpl.render(writer, session, group)

            return writer.to_string()

        def render_group_link(self, session, group):
            branch = session.branch()
            self.parent.param.set(branch, group)

            selected = self.parent.param.get(session) is group
            
            return mlink(branch.marshal(), "ServerGroup", group.name, selected)

    class BrowserServers(ServerSet):
        def get_items(self, session, group):
            if group:
                return sorted_by(group.server_items())
            else:
                return sorted_by(self.app.model.get_servers())

class ClusterBrowser(ItemSet):
    def __init__(self, app, name):
        super(ClusterBrowser, self).__init__(app, name)

        self.param = ClusterParameter(app, "cluster")
        self.add_parameter(self.param)

        self.view = ClusterView(app, "view")
        self.add_child(self.view)

    def get_items(self, session, model):
        return sorted_by(model.get_clusters())

    def render_item_link(self, session, cluster):
        class_ = self.param.get(session) is cluster and "selected"
        
        branch = session.branch()
        self.param.set(branch, cluster)
        return link(branch.marshal(), cluster.name, class_)

    def render_add_cluster_href(self, session, cluster):
        branch = session.branch()
        #self.page.show_cluster_add(branch)
        return branch.marshal()

    def render_edit_cluster_href(self, session, cluster):
        if cluster:
            branch = session.branch()
            #self.page.show_cluster_edit(branch, cluster)
            return branch.marshal()

    def render_remove_cluster_href(self, session, cluster):
        if cluster:
            branch = session.branch()
            return branch.marshal()

    def render_view(self, session, *args):
        object = self.param.get(session)

        if object:
            html = self.view.render(session)
        else:
            html = self.render_none(session, *args)

        return html

    def render_none(self, session, model):
        return none()

class BrokerConfigPropertyForm(CuminForm, Frame):
    def __init__(self, app, name):
        super(BrokerConfigPropertyForm, self).__init__(app, name)

        self.param = ConfigPropertyParameter(app, "param")
        self.add_parameter(self.param)

        self.source = Parameter(app, "source")
        self.source.default = "local"
        self.add_parameter(self.source)

        self.profile = RadioInput(app, "profile", self.source)
        self.profile.set_value("profile")
        self.add_child(self.profile)

        self.pvalue = StringInput(app, "profile_value")
        self.pvalue.set_disabled(True)
        self.add_child(self.pvalue)

        self.broker = RadioInput(app, "broker", self.source)
        self.broker.set_value("broker")
        self.add_child(self.broker)

        self.svalue = StringInput(app, "broker_value")
        self.svalue.set_disabled(True)
        self.add_child(self.svalue)

        self.local = RadioInput(app, "local", self.source)
        self.local.set_value("local")
        self.add_child(self.local)

        self.lvalue = StringInput(app, "local_value")
        self.add_child(self.lvalue)

    def render_title(self, session, prop):
        return "Edit Property '%s'" % prop.name

    def get_object(self, session):
        return self.param.get(session)

    def set_config_property(self, session, prop):
        return self.param.set(session, prop)

    def process_cancel(self, session, prop):
        branch = session.branch()
        self.page.show_broker(branch, prop.get_broker()).view.show(branch)
        self.page.redirect.set(session, branch.marshal())

    def process_submit(self, session, prop):
        source = self.source.get(session)
        
        if source == "profile":
            prop.value = get_profile_value(prop)
        elif source == "broker":
            prop.value = prop.broker_value
        elif source == "local":
            prop.value = self.lvalue.get(session)
        else:
            raise Exception()

        self.process_cancel(session, prop)

    def process_display(self, session, prop):
        self.pvalue.set(session, get_profile_value(prop))
        self.svalue.set(session, prop.broker_value)
        self.lvalue.set(session, prop.value)

class BrokerConfigTab(ConfigPropertySet):
    def render_title(self, session, broker):
        return "Configuration"

    def do_get_items(self, session, broker):
        return broker.properties

    def maybe_highlight(self, value, comparedto):
        if str(value) != str(comparedto):
            value = "<span class=\"BrokerConfigTab diff\">%s</span>" \
                    % value

        return value

    def render_item_broker_value(self, session, prop):
        return self.maybe_highlight(prop.broker_value, prop.value)

    def render_item_profile_value(self, session, prop):
        value = get_profile_value(prop)
        return self.maybe_highlight(value, prop.value)

    def render_item_edit_href(self, session, prop):
        branch = session.branch()
        frame = self.page.show_broker(branch, prop.get_broker())
        frame.show_config_property(branch, prop)
        return branch.marshal()

def get_profile_value(prop):
    profile = prop.get_broker().get_broker_profile()
    value = None

    if profile:
        for p in profile.config_property_items():
            if p.name == prop.name:
                value = p.value

    return value
