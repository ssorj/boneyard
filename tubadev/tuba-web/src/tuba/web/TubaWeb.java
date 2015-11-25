package tuba.web;

import java.io.*;
import java.net.*;
import java.util.*;
import lentil.*;
import tuba.runtime.*;
import tuba.runtime.model.*;
import tuba.util.*;
import wooly.*;
import wooly.lang.*;
import wooly.server.*;
import wooly.widgets.*;

public final class TubaWeb {
    private final int m_port;
    private final WoolyServer m_server;
    private final WoolyModel m_model;

    private TubaWeb(final int port) {
        m_port = port;
        m_server = WoolyServer.create(9090);
        m_model = new WoolyModel("tuba");

        final WoolyWidgetApplication root = new WoolyWidgetApplication
            ("root", null, m_model);
        m_server.setApplication(root);

        final URL url = TubaWeb.class.getResource("TubaWeb.wool");
        final WoolyPage page = (WoolyPage) WoolyParser.parse(url, m_model);
        page.setApplication(root);

        root.setWidget(page);

        // XXX the app-model rel is wrong
        final StaticFileApplication files = new StaticFileApplication
            ("files", root, m_model);
    }

    private static class TestWidget extends WoolyWidget {
        TestWidget(final String name, final WoolyModel model) {
            super(name, model);
        }

        protected void doRender(final WoolySession session,
                                final WoolyWriter writer) {
            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();

                final LentilCursor cursor = conn.load(Series.class);

                while (cursor.next()) {
                    final Series series = new Series();
		    conn.load(series, cursor);

                    writer.write(series.Title);
                    writer.write("<br/>");
                }
            } finally {
                conn.close();
            }
        }
    }

    private void run() throws IOException {
        m_server.run();
    }

    public static void main(final String[] args) throws IOException {
        int port = 9090;

        if (args.length == 1) {
            port = Integer.parseInt(args[0]);
        }

        final TubaRuntime runtime = Tuba.getRuntime();

        runtime.initialize();

        try {
            runtime.startup();

            new TubaWeb(port).run();
        } finally {
            runtime.shutdown();
        }
    }
}
