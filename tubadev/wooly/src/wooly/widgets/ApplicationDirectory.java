package wooly.widgets;

import java.util.*;
import wooly.*;

public class ApplicationDirectory extends WoolyWidget {
    public ApplicationDirectory(final String name) {
        super(name);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<ul>");

        renderApplication(session, writer, session.getApplication());

        writer.write("</ul>");
    }

    private void renderApplication(final WoolySession session,
                                   final WoolyWriter writer,
                                   final WoolyApplication app) {
        final String addr = app.getHttpAddress();
        final String name = app.getName();

        writer.write("<li>");
        writer.write("<a href=\"" + addr + "\">" + name + "</a>");
        writer.write("</li>");

        writer.write("<ul>");

        for (final WoolyApplication child : app.getChildren()) {
            renderApplication(session, writer, child);
        }

        writer.write("</ul>");
    }
}
