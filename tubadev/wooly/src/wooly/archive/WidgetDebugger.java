package wooly;

import java.util.*;
import java.util.logging.*;

public final class WidgetDebugger {
    private final WoolySession m_session;
    private final Map m_starts;
    private final Map m_ends;
    private String m_output;

    WidgetDebugger(final WoolySession session) {
        if (session == null) throw new IllegalArgumentException();

        m_session = session;
        m_starts = new HashMap();
        m_ends = new HashMap();
    }

    private WoolySession getSession() {
        return m_session;
    }

    public long getElapsedNanos(final WoolyWidget widget) {
        final Long start = (Long) m_starts.get(widget);
        final Long end = (Long) m_ends.get(widget);

        final long nanos;

        if (start == null) {
            nanos = -1;
        } else if (end == null) {
            nanos = -2;
        } else {
            nanos = end.longValue() - start.longValue();
        }

        return nanos;
    }

    public void beginRendering(final WoolyWidget widget) {
        final long now = System.nanoTime();

        m_starts.put(widget, new Long(now));
    }

    public void endRendering(final WoolyWidget widget) {
        final long now = System.nanoTime();

        m_ends.put(widget, new Long(now));
    }

    public String getOutput() {
        return m_output;
    }

    public void setOutput(final String output) {
        m_output = output;
    }
}
