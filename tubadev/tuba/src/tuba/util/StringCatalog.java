package tuba.util;

import java.io.*;
import java.net.*;
import java.util.*;

public final class StringCatalog {
    private final Map m_strings;

    public StringCatalog() {
        m_strings = new HashMap();
    }

    public StringCatalog(final Class clacc, final String resource) {
        this();

        try {
            final URL url = clacc.getResource(resource);

            if (url == null) throw new IllegalStateException
                ("Resource '" + resource + "' not found");

            load(url);
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }
    }

    public String get(final String key) {
        final String string = (String) m_strings.get(key);

        if (string == null) {
            throw new IllegalArgumentException
                ("No string found for key '" + key + "'");
        }

        return string;
    }

    public void load(final URL url) throws IOException {
        if (url == null) throw new IllegalArgumentException();

        load(new BufferedReader(new InputStreamReader(url.openStream())));
    }

    public void load(final BufferedReader reader) throws IOException {
        if (reader == null) throw new IllegalArgumentException();

        String line = null;
        String key = null;
        StringBuffer buffer = new StringBuffer();

        while ((line = reader.readLine()) != null) {
            if (line.startsWith("[") && line.endsWith("]")) {
                if (key != null) {
                    m_strings.put(key, rtrim(buffer.toString()));
                }

                buffer = new StringBuffer();

                key = line.substring(1, line.length() - 1);

                continue;
            }

            buffer.append(line + "\n");
        }

        m_strings.put(key, rtrim(buffer.toString()));
    }

    private String rtrim(final String string) {
        for (int i = string.length() - 1; i >= 0; i--) {
            if (!Character.isWhitespace(string.charAt(i))) {
                return string.substring(0, i + 1);
            }
        }

        return "";
    }
}
