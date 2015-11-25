package wooly.widgets;

import java.util.*;
import java.util.logging.*;
import wooly.*;

public class ButtonField extends FormWidget {
    private final Button m_button;
    private final Label m_label;

    public ButtonField(final String name,
                       final WoolyForm form) {
        super(name, form);

        m_button = new Button("button", form);
        m_label = new Label("label");

        addChild(m_button);
        addChild(m_label);
    }

    public final Label getLabel() {
        return m_label;
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<tr>");
        writer.write("<th></th>");
        writer.write("<td>" + m_button.render(session) + "</td>");
        writer.write("</tr>");
    }
}
