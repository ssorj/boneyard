package wooly.server;

import java.io.*;
import java.util.*;
import wooly.*;

public final class ServerResponse {
    private final ServerHeaders m_headers;
    private String m_body;

    ServerResponse() {
        m_headers = new ServerHeaders();
    }

    public String getBody() {
        return m_body;
    }

    public void setBody(final String body) {
        m_body = body;
    }

    void write(final BufferedWriter writer) throws IOException {
        writer.write("HTTP/1.1 200 OK\r\n");
        m_headers.write(writer);
        writer.write("\r\n");

        if (m_body != null) {
            writer.write(m_body);
        }

        writer.flush();
    }

    public ServerHeaders getHeaders() {
        return m_headers;
    }

    public void print() {
        System.out.println("S: HTTP/1.1 200 OK");
    }
}
