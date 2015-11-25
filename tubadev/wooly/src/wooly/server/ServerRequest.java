package wooly.server;

import java.io.*;
import java.net.*;
import java.util.*;
import wooly.*;

public final class ServerRequest {
    private final String m_method;
    private final URI m_uri;
    private final String m_protocol;
    private final ServerHeaders m_headers;

    private ServerRequest(final String method,
                         final URI uri,
                         final String protocol,
                         final ServerHeaders headers) {
        if (method == null) throw new IllegalArgumentException();
        if (uri == null) throw new IllegalArgumentException();
        if (protocol == null) throw new IllegalArgumentException();
        if (headers == null) throw new IllegalArgumentException();

        m_method = method;
        m_uri = uri;
        m_protocol = protocol;
        m_headers = headers;
    }

    static ServerRequest parse(final BufferedReader reader) throws IOException {
        final String line = reader.readLine();

        final String[] tokens = line.split(" ");

        final String method = tokens[0];
        final String suri = tokens[1];
        final String protocol = tokens[2];

        if (!method.equals("GET")) throw new UnsupportedOperationException();
        if (!suri.startsWith("/")) throw new IllegalStateException();

        final ServerHeaders headers = new ServerHeaders();
        headers.read(reader);

        final String host = headers.getHeader("host");

        if (host == null) throw new IllegalStateException();

        final URI uri;

        try {
            uri = new URI("http://" + host + suri);
        } catch (URISyntaxException e) {
            throw new IllegalStateException(e);
        }

        return new ServerRequest(method, uri, protocol, headers);
    }

    public String getMethod() {
        return m_method;
    }

    public URI getUri() {
        return m_uri;
    }

    public String getProtocol() {
        return m_protocol;
    }

    public ServerHeaders getHeaders() {
        return m_headers;
    }

    void print() {
        System.out.println
            ("C: " + getMethod() + " " + getUri() + " " + getProtocol());
    }
}
