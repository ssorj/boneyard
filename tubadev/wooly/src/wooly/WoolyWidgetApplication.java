package wooly;

import butyl.*;
import java.util.*;
import wheaty.*;
import wheaty.parameters.*;

public class WoolyWidgetApplication extends WoolyApplication {
    private WoolyWidget m_widget;
    private final StringParameter m_title;

    public WoolyWidgetApplication(final String name,
                                  final WoolyApplication parent,
                                  final WoolyModel model) {
        super(name, parent, model);

        m_title = new StringParameter("title");
        m_title.setTransient(true);

        model.addParameter(m_title);
    }

    public final WoolyWidget getWidget() {
        return m_widget;
    }

    public final void setWidget(final WoolyWidget widget) {
        m_widget = widget;
    }

    public final StringParameter getTitle() {
        return m_title;
    }

    protected WoolySession doProcess(final WoolyQuery query) {
        final WoolySession session = new WoolySession(this);

        // XXX or, move this work into process methods of individual
        // widgets
        getModel().unmarshal(query, session);

        getWidget().process(session, query);

        return session;
    }

    protected String doRender(final WoolySession session) {
        return getWidget().render(session);
    }
}
