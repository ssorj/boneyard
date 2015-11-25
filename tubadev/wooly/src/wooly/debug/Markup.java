package wooly.debug;

import java.io.*;
import java.util.*;
import org.jdom.*;
import org.jdom.input.*;
import org.jdom.output.*;
import wooly.*;
import wooly.widgets.*;

final class Markup extends WoolyWidget {
    public Markup(final String name, final WoolyModel model) {
        super(name, model);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        final String string = ""; // XXX session.getDebugger().getOutput();

        // XXX
        if (string == null) return;

        final SAXBuilder builder = new SAXBuilder();

        final Document doc;

        try {
            doc = builder.build(new StringReader(string));
        } catch (JDOMException e) {
            throw new IllegalStateException(e);
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }

        final StringWriter swriter = new StringWriter();

        final XMLOutputter out = new XMLOutputter
            (Format.getPrettyFormat());

        try {
            out.output(doc, swriter);
        } catch (IOException e) {
            throw new IllegalArgumentException(e.getMessage());
        }

        writer.write("<pre>");
        writer.write(out.escapeElementEntities(swriter.toString()));
        writer.write("</pre>");
    }
}
