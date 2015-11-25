package wooly;

import java.util.*;
import wheaty.*;
import wheaty.parameters.*;

public final class WoolySession extends WheatySession {
    // XXX move this to model
    private final WoolyApplication m_app;

    protected WoolySession(final WoolyApplication app) {
        super();

        if (app == null) throw new IllegalArgumentException();

        m_app = app;
    }

    protected WoolySession(final WoolySession orig) {
        super(orig);

        m_app = orig.getApplication();
    }

    public WoolySession branch() {
        return new WoolySession(this);
    }

    public WoolyApplication getApplication() {
        return m_app;
    }

    public final String href() {
        final WoolyWriter writer = new WoolyWriter();
        final WheatyDocument doc = new WheatyDocument();

        getApplication().getModel().marshal(this, doc);

        writer.write("?");

        for (final WheatyValue value : doc.getValues()) {
            value.traverse(new WheatyValue.Visitor() {
                    public void visit(final WheatyValue v) {
                        final String string = v.get();

                        if (string != null) {
                            final String path = v.getPath();
                            final int dot = path.indexOf(".");

                            if (dot != -1) {
                                writer.write(path.substring(dot + 1));
                                writer.write("=");
                                writer.write(string);
                                writer.write("&amp;");
                            }
                        }
                    }
                });
        }

        return writer.toString();
    }
}
