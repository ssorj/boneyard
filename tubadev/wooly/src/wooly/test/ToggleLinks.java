package wooly.test;

import java.util.*;
import wooly.*;
import wooly.widgets.*;

public class ToggleLinks extends WoolyWidget {
    private static final int s_dim = 3;

    private final ToggleLink[][] m_links;

    public ToggleLinks(final String name, final WoolyModel model) {
        super(name, model);

        m_links = new ToggleLink[s_dim][s_dim];

        for (int i = 0; i < s_dim; i++) {
            final ToggleLink[] row = m_links[i];

            for (int j = 0; j < s_dim; j++) {
                final int index = (i * s_dim) + j;

                final ToggleLink link = new ToggleLink("toggle" + index);
                add(link);

                final Label label = new Label("label");
                label.getText().set("Toggle " + index);
                link.add(label);

                row[j] = link;
            }
        }
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<table>");

        for (final ToggleLink[] row : m_links) {
            writer.write("<tr>");

            for (final ToggleLink link : row) {
                writer.write("<td>");
                writer.write(link.render(session));
                writer.write("</td>");
            }

            writer.write("</tr>");
        }

        writer.write("</table>");
    }
}
