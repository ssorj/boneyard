package wooly.widgets;

import java.io.*;
import java.net.*;
import java.util.*;
import wheaty.*;
import wheaty.parameters.*;
import wooly.*;

public class Text extends WoolyWidget {
    private final StringParameter m_text;

    public Text(final String name, final WoolyModel model) {
        super(name, model);

        m_text = new StringParameter(getPath());
        m_text.setTransient(true);

        model.addParameter(m_text);
    }

    public final StringParameter getText() {
        return m_text;
    }

    public final void setText(final String text) {
        m_text.set(text);
    }

    public final void setText(final URL url) {
        final StringWriter writer = new StringWriter();

        try {
            final Reader reader = new InputStreamReader(url.openStream());

            // XXX inefficient
            int c;
            while ((c = reader.read()) != -1) writer.write(c);
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }

        setText(writer.toString());
    }

    public final void setText(final WoolySession session, final String text) {
        m_text.set(session, text);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write((String) getText().get(session));
    }
}
