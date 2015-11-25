package wooly.widgets;

import wooly.*;

public class ApplicationContextPath extends WoolyWidget {
    public ApplicationContextPath(final String name) {
        super(name);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        final WoolyApplication app = session.getApplication();
        final WoolyApplication parent = app.getParent();

        if (parent != null) {
            render(session, writer, parent);
        }
    }

    private void render(final WoolySession session,
                        final WoolyWriter writer,
                        final WoolyApplication app) {
        final WoolyApplication parent = app.getParent();

        if (parent != null) {
            render(session, writer, parent);
        }

        writer.write("<a href=\"" + app.getHttpAddress() + "\">");
        writer.write(app.getName());
        writer.write("</a>");

        writer.write(" &gt; ");
    }
}
