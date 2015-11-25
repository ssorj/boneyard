package tuba.util;

import java.io.*;
import java.net.*;
import java.util.*;

public final class Template {
    private final String m_text;

    public Template(final String text) {
        m_text = text;
    }

    public Template(final Class clacc, final String resource) {
        final URL url = clacc.getResource(resource);

        if (url == null) throw new IllegalStateException
            ("Resource '" + resource + "' not found");

        final BufferedReader reader;

        try {
            reader = new BufferedReader
                (new InputStreamReader(url.openStream(), "UTF-8"));
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }

        final StringBuilder builder = new StringBuilder();

        try {
            String line;

            while ((line = reader.readLine()) != null) {
                builder.append(line);
            }
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }

        m_text = builder.toString();
    }

    public String interpolate(final Map vars) {
        return interpolate(m_text, vars);
    }

    private static String interpolate(final String text, final Map vars) {
        final StringBuilder builder = new StringBuilder(text.length() * 2);
        int start = 0;
        int end = text.indexOf('{');
        String ptext;

        while (true) {
            if (end == -1) {
                builder.append(text.substring(start));
                break;
            }

            builder.append(text.substring(start, end));

            start = text.indexOf('}', end + 1);

            if (start == -1) throw new IllegalArgumentException();

            ptext = text.substring(end + 1, start);

            if (ptext.length() == 0) {
                builder.append("{}");
            } else if (Character.isLetter(ptext.charAt(0))) {
                final String value = (String) vars.get(ptext);

                if (value != null) {
                    builder.append(value);
                }
            } else {
                // It's not a placeholder; keep the value as it was
                // before

                builder.append("{" + ptext + "}");
            }

            start = start + 1;
            end = text.indexOf('{', start);
        }

        return builder.toString();
    }
}
