package cedar;

import java.util.*;
import java.util.regex.*;

public final class CedarPath {
    private static final Pattern s_pattern = Pattern.compile("(.+?)(\\.|$)");

    private final String m_elem;
    private final CedarPath m_next;
    private final String m_string;

    private CedarPath(final String elem, final CedarPath next) {
        if (elem == null) throw new IllegalArgumentException();
        if (elem.equals("")) throw new IllegalArgumentException();
        if (elem.indexOf('.') != -1) throw new IllegalArgumentException();

        m_elem = elem;
        m_next = next;

        //System.out.println("CedarPath.m_elem = " + m_elem);
        //System.out.println("CedarPath.m_next = " + m_next);

        if (next() == null) {
            m_string = elem();
        } else {
            m_string = elem() + "." + next();
        }

        //s_cache.put(toString(), this);
    }

    public static CedarPath get(final String elem, final CedarPath path) {
        if (elem == null) throw new IllegalArgumentException();

        final String npath;

        if (path == null) {
            npath = elem;
        } else {
            npath = elem + "." + path;
        }

        return CedarPath.get(npath);
    }

    public static CedarPath get(final CedarPath path, final String elem) {
        if (path == null) throw new IllegalArgumentException();
        if (elem == null) throw new IllegalArgumentException();

        return CedarPath.get(path + "." + elem);
    }

    public static CedarPath get(final String path) {
        final CedarPath cpath;

        final Matcher matcher = s_pattern.matcher(path);

        if (matcher.find()) {
            cpath = CedarPath.get(path, matcher);
        } else {
            cpath = null;
        }

        return cpath;
    }

    private static CedarPath get(final String path, final Matcher matcher) {
        if (path == null) throw new IllegalArgumentException();
        if (matcher == null) throw new IllegalArgumentException();

        final String name = matcher.group(1);

        //System.out.println("name=" + name);

        CedarPath next = null;

        if (matcher.find()) {
            next = CedarPath.get(path, matcher);
        }

        return new CedarPath(name, next);
    }

    public String elem() {
        return m_elem;
    }

    public boolean hasNext() {
        return m_next != null;
    }

    public CedarPath next() {
        return m_next;
    }

    public void remove() {
        throw new UnsupportedOperationException();
    }

    public String toString() {
        return m_string;
    }

    public int hashCode() {
        return toString().hashCode();
    }

    public boolean equals(final Object other) {
        return other instanceof CedarPath &&
            toString().equals(other.toString());
    }
}
