package wooly.widgets;

import java.util.*;
import java.util.logging.*;
import wooly.*;

public class Button extends FormWidget {
    private static final Logger s_log = Logger.getLogger
        (Button.class.getName());

    public Button(final String name,
                  final WoolyModel model,
                  final WoolyForm form) {
        super(name, model, form);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<button");

//         if (!isEnabled(session)) {
//             writer.write(" disabled=\"disabled\"");
//         }

        writer.write(">");

        final Iterator children = getChildren().iterator();

        while (children.hasNext()) {
            final WoolyWidget child = (WoolyWidget) children.next();

            writer.write(child.render(session));
        }

        writer.write("</button>");
    }
}
