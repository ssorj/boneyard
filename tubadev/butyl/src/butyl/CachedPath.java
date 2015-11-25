package butyl;

import java.util.*;

public final class CachedPath {
    private static Map s_cache = new HashMap();

    private final String m_spath;
    private final String m_head;
    private final CachedPath m_tail;

    private CachedPath(final String spath) {
        m_spath = spath;

        final int sep = spath.indexOf(".");

        if (sep == -1) {
            m_head = spath;
            m_tail = null;
        } else {
            m_head = spath.substring(0, sep);
            m_tail = CachedPath.get(spath.substring(sep + 1));
        }

        synchronized (s_cache) {
            s_cache.put(spath, this);
        }
    }

    public static CachedPath get(final String spath) {
        CachedPath path;

        synchronized (s_cache) {
            path = (CachedPath) s_cache.get(spath);
        }

        if (path == null) {
            path = new CachedPath(spath);
        }

        return path;
    }

    public String head() {
        return m_head;
    }

    public CachedPath tail() {
        return m_tail;
    }

    public String toString() {
        return m_spath;
    }

    public int hashCode() {
        return toString().hashCode();
    }

    public boolean equals(final Object other) {
        return other instanceof CachedPath &&
            toString().equals(other.toString());
    }
}
