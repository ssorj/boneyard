package wooly.widgets;

import java.util.*;
import wheaty.*;
import wheaty.parameters.*;
import wooly.*;

public class ToggleLink extends WoolyLink {
    private final BooleanParameter m_enabled;

    public ToggleLink(final String name) {
        super(name);

        m_enabled = new BooleanParameter(getPath());
        m_enabled.setNullable(false);
        m_enabled.set(Boolean.FALSE);

        getModel().addParameter(m_enabled);
    }

    public BooleanParameter getEnabled() {
        return m_enabled;
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        final boolean enabled =
            ((Boolean) m_enabled.get(session)).booleanValue();

        if (enabled) {
            writer.write("<b>");
        }

        writer.write("<a href=\"?");

        final WoolySession branch = session.branch();

        m_enabled.set(branch, new Boolean(!enabled));

        writer.write(branch.href());

        writer.write("\">");

        renderContents(session, writer);

        writer.write("</a>");

        if (enabled) {
            writer.write("</b>");
        }
    }
}
