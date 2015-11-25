package wooly.widgets;

import java.util.*;
import wooly.*;

public final class Tabs extends WoolyWidget {
    private ModalPane m_modes;
    private final Map m_map;

    public Tabs(final String name, final WoolyModel model) {
        super(name, model);

        m_map = new HashMap();
    }

    public void setModes(final ModalPane modes) {
        m_modes = modes;
    }

    public ModalPane getModes() {
        return m_modes;
    }

    public final void map(final WoolyWidget tab, final WoolyWidget mode) {
        if (tab == null) throw new IllegalArgumentException();
        if (mode == null) throw new IllegalArgumentException();

        m_map.put(tab, mode);
    }

    private WoolyWidget getMode(final WoolyWidget tab) {
        return (WoolyWidget) m_map.get(tab);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        final StringBuilder builder = new StringBuilder();

        final Iterator children = getChildren().iterator();

        while (children.hasNext()) {
            final WoolyWidget tab = (WoolyWidget) children.next();
            final WoolySession branch = session.branch();

            getModes().setMode(branch, getMode(tab));

            builder.append("<div class=\"tab\">");
            builder.append("<a href=\"" + branch.href() + "\">");
            builder.append(tab.render(session));
            builder.append("</a>");
            builder.append("</div>");
        }

        final int len = builder.length();

        writer.write("<div class=\"tabset\">");

        if (builder.length() > 0) {
            writer.write(builder.toString());
        }

        writer.write("</div>");
    }
}
