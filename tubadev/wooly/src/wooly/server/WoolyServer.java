package wooly.server;

import butyl.*;
import java.io.*;
import java.net.*;
import java.util.*;
import wooly.*;

public final class WoolyServer {
    private final InetSocketAddress m_addr;
    private WoolyApplication m_app;

    private WoolyServer(final InetSocketAddress addr) {
        if (addr == null) throw new IllegalArgumentException();

        m_addr = addr;
    }

    public static WoolyServer create(final int port) {
        return new WoolyServer(new InetSocketAddress(port));
    }

    public InetSocketAddress getAddress() {
        return m_addr;
    }

    public String getLocation() {
        final String host = getAddress().getHostName();
        final int port = getAddress().getPort();
        final String location;

        if (port == 80) {
            location = "http://" + host;
        } else {
            location = "http://" + host + ":" + port;
        }

        return location;
    }

    public WoolyApplication getApplication() {
        return m_app;
    }

    public void setApplication(final WoolyApplication app) {
        m_app = app;
    }

    public void run() throws IOException {
        final ServerSocket server = new ServerSocket();

        try {
            server.bind(getAddress());

            System.out.println(server);

            while (true) {
                final Socket conn = server.accept();
                final RequestHandler handler = new RequestHandler(conn);
                new Thread(handler).start();
            }
        } finally {
            server.close();
        }
    }

    private class RequestHandler implements Runnable {
        private final Socket m_conn;

        RequestHandler(final Socket conn) {
            m_conn = conn;
        }

        public void run() {
            try {
                final InputStream in = m_conn.getInputStream();
                final OutputStream out = m_conn.getOutputStream();

                final BufferedReader reader = new BufferedReader
                    (new InputStreamReader(in));
                final BufferedWriter writer = new BufferedWriter
                    (new OutputStreamWriter(out));

                final ServerRequest req = ServerRequest.parse(reader);
                final ServerResponse resp = new ServerResponse();

                req.print();

                final String spath = req.getUri().getPath();
                final String[] pelems = spath.split("/", 0);

                System.out.println("spath = " + spath);
                System.out.println("pelems = " + Arrays.asList(pelems));

                WoolyApplication app = getApplication();
                String page = null;

                switch (pelems.length) {
                case 0:
                case 1:
                    break;
                case 2:
                    CachedPath path = CachedPath.get(pelems[1]);
                    WoolyApplication capp;

                    do {
                        capp = app.getChild(path.head());

                        if (capp == null) break;

                        app = capp;
                    } while ((path = path.tail()) != null);
                case 3:
                    page = pelems[2];
                }

                final WoolyQuery query = new WoolyQuery(page);
                final String squery = req.getUri().getQuery();

                if (squery != null) {
                    query.parse(UrlCodec.decode(squery));
                }

                final WoolySession session = app.process(query);
                // XXX Make decisions here
                final String body = app.render(session);

                resp.setBody(body);

                resp.print();

                resp.write(writer);

                writer.close();
            } catch (IOException e) {
                throw new IllegalStateException(e);
            } finally {
                try {
                    m_conn.close();
                } catch (IOException e) {
                    // Hmmm XXX
                }
            }
        }
    }
}
