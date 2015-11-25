package wooly;

import java.util.*;
import wheaty.*;

public class WoolyLink extends WoolyWidget {
    public WoolyLink(final String name) {
        super(name);
    }

    protected void renderContents(final WoolySession session,
                                  final WoolyWriter writer) {
        for (final WoolyWidget child : getChildren()) {
            writer.write(child.render(session));
        }
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<a href=\"?");
        writer.write(session.href());
        writer.write("\">");

        renderContents(session, writer);

        writer.write("</a>");
    }
}
