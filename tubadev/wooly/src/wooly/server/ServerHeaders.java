package wooly.server;

import java.io.*;
import java.net.*;
import java.text.*;
import java.util.*;
import wooly.*;

// * Handle multi-line headers
// * Consider using a String[] instead of List<String> for values
// * Add name validation
final class ServerHeaders {
    private final Map m_headers;
    private final DateFormat m_formatter;

    ServerHeaders() {
        m_headers = new LinkedHashMap();
        m_formatter = new SimpleDateFormat("EEE, dd MMM yyyy HH:mm:ss 'GMT'");
    }

    private DateFormat formatter() {
        return m_formatter;
    }

    // XXX This doesn't try to deal with multi-line headers
    void read(final BufferedReader reader) throws IOException {
        String line = reader.readLine();

        while (!line.equals("")) {
            final int sep = line.indexOf(':');

            if (sep == -1) {
                throw new IllegalStateException();
            }

            final String name = line.substring(0, sep).toLowerCase();

            List values = getHeaderValues(name);

            if (values == null) {
                values = new ArrayList();
                setHeaderValues(name, values);
            }

            values.add(line.substring(sep + 1).trim());

            line = reader.readLine();
        }
    }

    void write(final BufferedWriter writer) throws IOException {
        final Iterator entries = m_headers.entrySet().iterator();

        while (entries.hasNext()) {
            final Map.Entry entry = (Map.Entry) entries.next();
            final String key = (String) entry.getKey();
            final Iterator values = ((List) entry.getValue()).iterator();

            while (values.hasNext()) {
                final String value = (String) values.next();

                writer.write(key);
                writer.write(": ");
                writer.write(value);
                writer.write("\r\n");
            }
        }
    }

    public boolean containsHeader(final String name) {
        return m_headers.containsKey(name.toLowerCase());
    }

    private List getHeaderValues(final String name) {
        if (name == null) throw new IllegalArgumentException();

        final List values = (List) m_headers.get(name.toLowerCase());

        if (values == null) {
            return null;
        }

        return values;
    }

    private void setHeaderValues(final String name, final List values) {
        if (name == null) throw new IllegalArgumentException();
        if (values == null) throw new IllegalArgumentException();

        m_headers.put(name.toLowerCase(), values);
    }

    public void addHeader(final String name, final String value) {
        List values = getHeaderValues(name);

        if (values == null) {
            values = new ArrayList();
            setHeaderValues(name, values);
        }

        values.add(value);
    }

    public String getHeader(final String name) {
        final List values = getHeaderValues(name);

        if (values == null) {
            return null;
        }

        // XXX This case isn't right
        if (values.size() == 0) {
            return null;
        }

        return (String) values.get(0);
    }

    public void setHeader(final String name, final String value) {
        final List values = new ArrayList();
        values.add(value);

        setHeaderValues(name, values);
    }

    public long getDateHeader(final String name) {
        final String value = getHeader(name);

        if (value == null) {
            return -1;
        }

        final Date date;

        try {
            date = formatter().parse(value);
        } catch (ParseException e) {
            throw new IllegalStateException(e);
        }

        return date.getTime();
    }

    public void setDateHeader(final String name, final long time) {
        setHeader(name, formatter().format(new Date(time)));
    }

    public void addDateHeader(final String name, final long time) {
        addHeader(name, formatter().format(new Date(time)));
    }

    public int getIntHeader(final String name) {
        final String value = getHeader(name);

        if (value == null) {
            return -1;
        }

        return Integer.parseInt(value);
    }

    public void setIntHeader(final String name, final int value) {
        setHeader(name, String.valueOf(value));
    }

    public void addIntHeader(final String name, final int value) {
        addHeader(name, String.valueOf(value));
    }

    public Enumeration getHeaderNames() {
        return Collections.enumeration(m_headers.keySet());
    }

    public Enumeration getHeaders(final String name) {
        return Collections.enumeration(getHeaderValues(name));
    }

    void print() {
        final Iterator iter = m_headers.entrySet().iterator();

        while (iter.hasNext()) {
            final Map.Entry entry = (Map.Entry) iter.next();

            System.out.println(entry.getKey() + " " + entry.getValue());
        }
    }
}
