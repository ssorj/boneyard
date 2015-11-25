package wooly;

import java.util.*;
import wheaty.*;

public class WoolyForm extends WoolyWidget {
    private final SessionLocal m_doc;

    public WoolyForm(final String name) {
        super(name);

        m_doc = new SessionLocal(getPath());
    }

    public final SessionLocal getDocument() {
        return m_doc;
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
//         final WheatyDocument doc = new WheatyDocument();
//         getModel().marshal(session, doc);

//         getDocument().set(session, doc);

//         writer.write("<form");
//         writer.write(" action=\"?\"");
//         writer.write(" method=\"get\"");
//         writer.write(">");
//         writer.write("<table>");

//         for (final WoolyWidget child : getChildren()) {
//             writer.write(child.render(session));
//         }

//         writer.write("</table>");

//         for (final WheatyValue value : doc.getValues()) {
//             value.traverse(new WheatyValue.Visitor() {
//                     public void visit(final WheatyValue v) {
//                         final String string = v.get();

//                         if (string != null) {
//                             writer.write("<input");
//                             writer.write(" type=\"hidden\"");
//                             writer.write(" name=\"" + v.getPath() + "\"");
//                             writer.write(" value=\"" + string + "\"");
//                             writer.write("/>");
//                         }
//                     }
//                 });
//         }

//         writer.write("</form>");
    }
}
