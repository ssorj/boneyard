package wooly;

import java.util.*;
import java.util.regex.*;
import wheaty.*;
import wheaty.parameters.*;

public final class WoolyQuery extends WheatyDocument {
    private static final Pattern s_pattern = Pattern.compile
            ("(.*?)\\=(.*?)(\\&|$)");

    private final String m_page;

    public WoolyQuery(final String page) {
        super();

        m_page = page;
    }

    public String getPage() {
        return m_page;
    }

    // Expects a decoded query string
    public void parse(final String squery) {
        if (squery == null) throw new IllegalArgumentException();

        final Matcher matcher = s_pattern.matcher(squery);

        while (matcher.find()) {
            final String path = matcher.group(1);
            final String[] elems = path.split("\\.");
            WheatyValue parent = null;

            for (final String elem : elems) {
                final WheatyValue child = new WheatyValue(elem);

                if (parent == null) {
                    addValue(child);
                } else {
                    parent.addChild(child);
                }

                parent = child;
            }

            parent.set(matcher.group(2));
        }
    }
}
