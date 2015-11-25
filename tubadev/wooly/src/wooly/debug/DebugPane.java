package wooly.debug;

import java.util.*;
import wooly.*;
import wooly.widgets.*;

public final class DebugPane extends WoolyContainer {
    public DebugPane(final String name) {
        super(name);

        final TabbedPane tabs = new TabbedPane("tabs");
        add(tabs);

        tabs.addTab(new WidgetTree("widgets"), "Widgets");
        tabs.addTab(new WidgetProfile("profile"), "Profile");
        tabs.addTab(new WidgetParameters("params"), "Parameters");
        tabs.addTab(new Markup("markup"), "Markup");
    }
}
