package wooly;

import java.net.*;
import java.util.*;

public final class WoolyWriter {
    private final StringBuilder m_builder;

    public WoolyWriter() {
        m_builder = new StringBuilder();
    }

    public void write(final String string) {
        m_builder.append(string);
    }

    public String toString() {
        return m_builder.toString();
    }
}
