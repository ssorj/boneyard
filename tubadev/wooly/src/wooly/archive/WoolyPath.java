package wooly;

import java.util.*;
import java.util.logging.*;

public final class WoolyPath {
    private static final Logger s_log = Logger.getLogger
        (WoolyPath.class.getName());

    private static final boolean s_cacheEnabled = false;
    private static final Map s_cache = Collections.synchronizedMap
        (new HashMap());

    private final String m_head;
    private final WoolyPath m_tail;
    private final String m_string;

    private WoolyPath(final String head, final WoolyPath tail) {
        if (head == null) throw new IllegalArgumentException();

        m_head = head;
        m_tail = tail;

        if (tail() == null) {
            m_string = head();
        } else {
            m_string = head() + "." + tail();
        }

        s_cache.put(toString(), this);
    }

    static final WoolyPath get(final String head, final WoolyPath tail) {
        if (head == null) throw new IllegalArgumentException();
        if (head.indexOf('.') != -1) throw new IllegalArgumentException();

        final WoolyPath path;

        if (tail == null) {
            path = WoolyPath.get(head);
        } else {
            path = WoolyPath.get(head + "." + tail);
        }

        return path;
    }

    static final WoolyPath get(final String path) {
        if (path == null) throw new IllegalArgumentException();

        WoolyPath wpath = null;

        if (s_cacheEnabled == true) {
            wpath = (WoolyPath) s_cache.get(path);
        }

        if (wpath == null) {
            final int sep = path.indexOf('.');

            if (sep == -1) {
                wpath = new WoolyPath(path, null);
            } else {
                final String head = path.substring(0, sep);
                final String tail = path.substring(sep + 1);

                wpath = new WoolyPath(head, WoolyPath.get(tail));
            }
        }

        return wpath;
    }

    public String head() {
        return m_head;
    }

    public WoolyPath tail() {
        return m_tail;
    }

    public String toString() {
        return m_string;
    }

    public int hashCode() {
        return toString().hashCode();
    }

    public boolean equals(final Object other) {
        return other instanceof WoolyPath &&
            toString().equals(other.toString());
    }
}

//     // XXX kinda lame
//     WoolyPath concat(final WoolyPath addition) {
//         return WoolyPath.get(toString() + "." + addition.toString());
//     }

//     private static WoolyPath create(final String head, final WoolyPath tail) {
//         return new WoolyPath(head, tail);
//     }

//     private static WoolyPath create(WoolyObject object) {
//         WoolyPath path = s_empty;

//         while (object != null) {
//             path = new WoolyPath(object.getName(), path);
//             object = object.getParent();
//         }

//         return path;
//     }

