package wooly.debug;

import java.text.*;
import java.util.*;
import wooly.*;

final class WidgetProfile extends WoolyWidget {
    public WidgetProfile(final String name, final WoolyModel model) {
        super(name, model);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<table>");

//         report(session.getDebugger(),
//                session.getApplication().getWidget(), 0, writer);

        writer.write("</table>");
    }

//     private void report(final WidgetDebugger debug,
//                         final WoolyWidget widget,
//                         final int level,
//                         final WoolyWriter writer) {
//         final DecimalFormat format = new DecimalFormat();
//         format.setMinimumFractionDigits(3);
//         format.setMaximumFractionDigits(3);

//         final long cummulative = debug.getElapsedNanos(widget);

//         Iterator children = widget.getChildren().iterator();
//         long self = cummulative;

//         while (children.hasNext()) {
//             final WoolyWidget child = (WoolyWidget) children.next();

//             self -= debug.getElapsedNanos(child);
//         }

//         writer.write("<tr>");
//         writer.write("<td>" + widget.getName() + "</td>");
//         writer.write("<td style=\"text-align: right\">" +
//                      format.format(cummulative / 1000000f) + "</td>");
//         writer.write("<td style=\"text-align: right\">" +
//                      format.format(self / 1000000f) + "</td>");
//         writer.write("</tr>");

//         children = widget.getChildren().iterator();

//         while (children.hasNext()) {
//             final WoolyWidget child = (WoolyWidget) children.next();

//             report(debug, child, level + 1, writer);
//         }
//     }
}
