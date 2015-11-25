package wooly.widgets;

import java.util.*;
import wheaty.*;
import wheaty.parameters.*;
import wooly.*;

public class ModalPane extends WoolyWidget {
    private final StringParameter m_key;

    public ModalPane(final String name) {
        super(name, model);

        m_key = new StringParameter("mode");

        final WheatyModel model = new WheatyModel(getPath());
        model.addParameter(m_key);
    }

    public final WoolyWidget getMode(final WoolySession session) {
        if (session == null) throw new IllegalArgumentException();
        if (getChildren().size() == 0) throw new IllegalStateException();

        final String key = (String) m_key.get(session);
        final WoolyWidget mode = getChild(key);

        return mode;
    }

    public final void setMode(final WoolySession session,
                              final WoolyWidget mode) {
        if (session == null) throw new IllegalArgumentException();
        if (mode == null) throw new IllegalArgumentException();

        m_key.set(session, mode.getName());
    }

    protected void doProcess(final WoolySession session,
                             final WoolyQuery query) {
        final WoolyWidget mode = getMode(session);

        if (mode != null) {
            mode.process(session, query);
        }
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        final WoolyWidget mode = getMode(session);

        writer.write("<div class=\"mode\">");

        if (mode != null) {
            writer.write(mode.render(session));
        }

        writer.write("</div>");
    }
}
