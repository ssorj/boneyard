package wooly.widgets;

import java.util.*;
import wheaty.*;
import wheaty.parameters.*;
import wooly.*;

public class Label extends WoolyWidget {
    private final StringParameter m_text;

    public Label(final String name) {
        super(name);

        m_text = new StringParameter(getPath());
        m_text.setTransient(true);
    }

    public final StringParameter getText() {
        return m_text;
    }

    public final void setText(final String text) {
        m_text.set(text);
    }

    public final void setText(final WoolySession session, final String text) {
        m_text.set(session, text);
    }

    protected void doInitialize(final WoolyModel model) {
        model.addParameter(m_text);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write((String) getText().get(session));
    }
}
