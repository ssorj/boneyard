package wooly;

import java.util.*;
import wheaty.*;
import wheaty.parameters.*;

public class WoolyPage extends WoolyWidget {
    private final StringParameter m_title;
//     private final StringParameter m_style;
    private WoolyApplication m_app;

    public WoolyPage(final String name) {
        super(name);

        m_title = new StringParameter(getPath());
        m_title.setTransient(true);

//         m_style = new StringParameter("style");
//         m_style.setParent(getParameter());
//         m_style.setTransient(true);
    }

    public WoolyPage(final String name,
                     final WoolyApplication app) {
        this(name);

        if (app == null) throw new IllegalArgumentException();

        setApplication(app);
    }

    public final WoolyApplication getApplication() {
        return m_app;
    }

    public final void setApplication(final WoolyApplication app) {
        if (app == null) throw new IllegalArgumentException();
        if (m_app != null) throw new IllegalStateException();

        m_app = app;
    }

    public final StringParameter getTitle() {
        return m_title;
    }

    protected void doProcess(final WoolySession session,
                             final WoolyQuery query) {
        for (final WoolyWidget child : getChildren()) {
            child.process(session, query);
        }
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<html><head><title>");
        writer.write((String) m_title.get(session));
        writer.write("</title><link href=\"file:///tmp/style.css\" rel=\"stylesheet\"/></head><body>");

        for (final WoolyWidget child : getChildren()) {
            writer.write(child.render(session));
        }

        writer.write("</body></html>");
    }
}
