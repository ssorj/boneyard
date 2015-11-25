package wooly.widgets;

import java.util.*;
import wooly.*;

public final class TabbedPane extends WoolyWidget {
    private final ModalPane m_modes;
    private final Tabs m_tabs;
    private final WoolyLink m_link;
    private final Map m_map;
    private final Map m_rmap;

    public TabbedPane(final String name) {
        super(name, model);

        m_modes = new ModalPane("_m", model);
        addChild(m_modes);

        m_tabs = new Tabs("_t", model);
        addChild(m_tabs);

        m_link = new WoolyLink("link", model) {
                protected void renderContents(final WoolySession session,
                                              final WoolyWriter writer) {
                    final WoolyWidget tab = getTab(m_modes.getMode(session));

                    writer.write(tab.render(session));
                }
            };
        addChild(m_link);

        m_map = new HashMap();
        m_rmap = new HashMap();
    }

    private WoolyWidget getTab(final WoolyWidget mode) {
        if (mode == null) throw new IllegalArgumentException();

        final WoolyWidget tab = (WoolyWidget) m_map.get(mode);

        if (tab == null) throw new IllegalStateException();

        return tab;
    }

    private WoolyWidget getMode(final WoolyWidget tab) {
        if (tab == null) throw new IllegalArgumentException();

        final WoolyWidget mode = (WoolyWidget) m_rmap.get(tab);

        if (mode == null) throw new IllegalStateException();

        return mode;
    }

    public void addTab(final WoolyWidget mode, final WoolyWidget tab) {
        if (mode == null) throw new IllegalArgumentException();
        if (tab == null) throw new IllegalArgumentException();

        m_tabs.add(tab);
        m_modes.add(mode);

        m_map.put(mode, tab);
        m_rmap.put(tab, mode);
    }

    public void addTab(final WoolyWidget mode, final String tab) {
        final String name = "label" + m_tabs.getChildren().size();
        final Label label = new Label(name, getModel());
        label.getText().set(tab);

        addTab(mode, label);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<div>");
        writer.write(m_tabs.render(session));
        writer.write("</div>");

        writer.write("<div>");
        writer.write(m_modes.render(session));
        writer.write("</div>");
    }

    private class Tabs extends WoolyWidget {
        Tabs(final String name) {
            super(name);
        }

        private boolean isSelected(final WoolySession session,
                                   final WoolyWidget widget) {
            final WoolyWidget tab = getTab(m_modes.getMode(session));

            return widget.equals(tab);
        }

        protected void doRender(final WoolySession session,
                                final WoolyWriter writer) {
            final StringBuilder builder = new StringBuilder();

            for (final WoolyWidget tab : getChildren()) {
                final boolean selected = isSelected(session, tab);

                if (selected) {
                    builder.append("<b>");
                }

                final WoolySession branch = session.branch();

                m_modes.setMode(branch, getMode(tab));
                builder.append(m_link.render(branch));

                if (selected) {
                    builder.append("</b>");
                }

                builder.append(" | ");
            }

            final int len = builder.length();

            if (len >= 4) {
                writer.write(builder.substring(0, len - 4));
            }
        }
    }
}
