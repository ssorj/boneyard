package wooly;

import java.io.*;
import java.net.*;
import java.util.*;
import java.util.logging.*;

public final class WidgetTemplate {
    private static final Logger s_log = Logger.getLogger
        (WidgetTemplate.class.getName());

    private final String m_name;
    private final WoolyWidget m_widget;
    private final Map m_templates;

    private WidgetTemplate(final String name, final WoolyWidget widget) {
        if (name == null) throw new IllegalArgumentException();
        if (widget == null) throw new IllegalArgumentException();

        m_name = name;
        m_widget = widget;
        m_templates = Collections.synchronizedMap(new HashMap());
    }

    public static WidgetTemplate load(final String name,
                                      final WoolyWidget widget,
                                      final String file) {
        final WidgetTemplate template = new WidgetTemplate(name, widget);

        try {
            template.load(file);
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }

        return template;
    }

    public String getName() {
        return m_name;
    }

    public WoolyWidget getWidget() {
        return m_widget;
    }

    private Map getTemplates() {
        return m_templates;
    }

    public String getPath() {
        return getWidget().getPath() + "." + getName();
    }

    public String get(final String key) {
        if (key == null) throw new IllegalArgumentException();

        final String value = (String) getTemplates().get(key);

        if (value == null) {
            throw new IllegalArgumentException
                ("Key '" + key + "' has no value");
        }

        return value;
    }

    public String get(final String key, final Map vars) {
        if (vars == null) throw new IllegalStateException();

        return interpolate(get(key), vars);
    }

    private void load(final String file) throws IOException {
        final List classes = new ArrayList();
        Class clacc = getWidget().getClass();

        while (clacc != null) {
            final URL resource = clacc.getResource(file);

            if (resource != null) {
                load(new BufferedReader
                     (new InputStreamReader(resource.openStream())));
                return;
            }

            clacc = clacc.getSuperclass();
        }
    }

    private void load(final BufferedReader reader) throws IOException {
        if (reader == null) throw new IllegalArgumentException();

        String line = null;
        String key = null;
        StringBuffer message = new StringBuffer();

        while ((line = reader.readLine()) != null) {
            if (line.startsWith("[") && line.endsWith("]")) {
                if (key != null) {
                    getTemplates().put(key, rtrim(message.toString()));
                }

                message = new StringBuffer();

                key = line.substring(1, line.length() - 1);

                continue;
            }

            message.append(line + "\n");
        }

        getTemplates().put(key, rtrim(message.toString()));
    }

    private String rtrim(final String string) {
        for (int i = string.length() - 1; i >= 0; i--) {
            if (!Character.isWhitespace(string.charAt(i))) {
                return string.substring(0, i + 1);
            }
        }

        return "";
    }

    private String interpolate(final String text, final Map vars) {
        final StringBuffer buffer = new StringBuffer(text.length() * 2);
        int start = 0;
        int end = text.indexOf('{');
        String ptext;

        while (true) {
            if (end == -1) {
                buffer.append(text.substring(start));
                break;
            }

            buffer.append(text.substring(start, end));

            start = text.indexOf('}', end + 1);

            if (start == -1) throw new IllegalArgumentException();

            ptext = text.substring(end + 1, start);

            if (ptext.length() == 0) {
                buffer.append("{}");
            } else if (Character.isLetter(ptext.charAt(0))) {
                final String value = (String) vars.get(ptext);

                if (value != null) {
                    buffer.append(value);
                }
            } else {
                // It's not a placeholder; keep the value as it was
                // before

                buffer.append("{" + ptext + "}");
            }

            start = start + 1;
            end = text.indexOf('{', start);
        }

        return buffer.toString();
    }
}
