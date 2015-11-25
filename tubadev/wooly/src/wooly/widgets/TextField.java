package wooly.widgets;

import java.util.*;
import wooly.*;

public class TextField extends FormWidget {
    private final Label m_label;
    private final TextEntry m_entry;

    public TextField(final String name,
                     final WoolyModel model,
                     final WoolyForm form) {
        super(name, model, form);

        m_label = new Label("label", model);
        m_label.setParent(this);

        m_entry = new TextEntry("entry", model, form);
        m_entry.setParent(this);
    }

    public final Label getLabel() {
        return m_label;
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<tr>");
        writer.write("<td><label for=\"" +
                     m_entry.getText().getPath() +
                     "\">" +
                     getLabel().render(session) +
                     "</label></td>");
        writer.write("<td>" + m_entry.render(session) + "</td>");
        writer.write("</tr>");
    }
}
