package lentil;

import java.io.*;
import java.util.*;

class Session {
    private final String m_name;

    private int m_threshold;
    private boolean m_debug;
    private boolean m_open;
    private final PrintWriter m_out;

    public Session(final String name) {
        m_name = name;

        m_threshold = 1;
        m_debug = false;
        m_open = false;
        m_out = new PrintWriter(System.out, true);
    }

    public final String getName() {
        return m_name;
    }

    public final int getLoggingThreshold() {
        return m_threshold;
    }

    public final void setLoggingThreshold(final int threshold) {
        m_threshold = threshold;
    }

    public final void log(final String message) {
        log(0, message);
    }

    public final void log(final int threshold, final String message) {
        if (threshold <= getLoggingThreshold()) {
            m_out.println(getName() + ": " + message);
        }
    }

    public final boolean isOpen() {
        return m_open;
    }

    public void open() {
        log(1, "Opening session '" + getName() + "'");

        if (isOpen()) {
            throw new IllegalStateException("Session already opened");
        }

        m_open = true;
    }

    public void close() {
        log(1, "Closing session '" + getName() + "'");

        if (!isOpen()) {
            throw new IllegalStateException("Session already closed");
        }

        m_open = false;
    }

    public final boolean isDebugEnabled() {
        return m_debug;
    }

    public final void setDebugEnabled(final boolean debug) {
        m_debug = debug;
    }
}
