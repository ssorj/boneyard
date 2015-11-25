package wooly.widgets;

import java.util.*;
import wheaty.*;
import wheaty.parameters.*;
import wooly.*;

public class TextEntry extends FormWidget {
    private final StringParameter m_text;

    public TextEntry(final String name,
                     final WoolyModel model,
                     final WoolyForm form) {
        super(name, model, form);

        m_text = new StringParameter(getPath());
        m_text.setNullable(false);
        m_text.set("");

        model.addParameter(m_text);
    }

    public final StringParameter getText() {
        return m_text;
    }

    protected void doProcess(final WoolySession session,
                             final WoolyQuery query) {
        super.doProcess(session, query);

        if (!getText().isSet(session)) {
            getText().set(session, getText().get());
        }
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        final WheatyDocument doc = (WheatyDocument)
            getForm().getDocument().get(session);
        final WheatyValue value = doc.getValue(getText().getPath());

        writer.write("<input");
        writer.write(" name=\"" + value.getPath() + "\"");
        writer.write(" type=\"text\"");
        writer.write(" value=\"" + value.get() + "\"");
        writer.write("/>");

        // XXX
        //value.remove();
    }
}
