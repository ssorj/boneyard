package wooly.debug;

import java.util.*;
import wooly.*;

final class WidgetTree extends WoolyWidget {
    public WidgetTree(final String name, final WoolyModel model) {
        super(name, model);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<pre>");

        report(session.getApplication().getWidget(), 0, writer);

        writer.write("</pre>");
    }

    private void report(final WoolyWidget widget,
                        final int level,
                        final WoolyWriter writer) {
        indent(level, writer);

        writer.write("widget <b>" + widget.getName() + "</b> {\n");

        final Iterator children = widget.getChildren().iterator();

        while (children.hasNext()) {
            final WoolyWidget child = (WoolyWidget) children.next();

            report(child, level + 1, writer);
        }

        indent(level, writer);
        writer.write("}\n");
    }

    private void indent(final int level, final WoolyWriter writer) {
        for (int i = 0; i < level; i++) {
            writer.write("  ");
        }
    }
}
