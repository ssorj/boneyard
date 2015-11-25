package wooly.debug;

import cedar.*;
import java.util.*;
import wooly.*;

final class WidgetParameters extends WoolyWidget {
    public WidgetParameters(final String name, final WoolyModel model) {
        super(name, model);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<table>");

        render(session, session.getApplication().getWidget(), 0, writer);

        writer.write("</table>");
    }

    private void render(final WoolySession session,
                        final WoolyWidget widget,
                        final int level,
                        final WoolyWriter writer) {
        final List list = new ArrayList();

        // XXX all broken
//         new CedarTraversal<WoolyWidget>() {
//             protected final void visit(final WoolyWidget widget,
//                                        final int depth) {
//                 list.add(widget.getParameter());
//             }
//         }.run(widget);

//         final Iterator params = list.iterator();

//         while (params.hasNext()) {
//             final WoolyParameter param = (WoolyParameter) params.next();

//             writer.write("<tr>");
//             writer.write("<td>" + widget.getPath() + "</td>");
//             writer.write("<td>" + param.getName() + "</td>");
//             writer.write("<td>" + param.get(session) + "</td>");
//             writer.write("<td>" + "" + "</td>");
//             writer.write("</tr>");
//         }

//         final Iterator children = widget.getChildren().iterator();

//         while (children.hasNext()) {
//             final WoolyWidget child = (WoolyWidget) children.next();

//             render(session, child, level + 1, writer);
//         }
    }
}
