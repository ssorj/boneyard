package wooly;

import butyl.*;
import java.util.*;
import wheaty.*;
import wheaty.parameters.*;

public class StaticFileApplication extends WoolyApplication {
    private final StringParameter m_file;

    public StaticFileApplication(final String name,
                                 final WoolyApplication parent,
                                 final WoolyModel model) {
        super(name, parent, model);

        m_file = new StringParameter("file");
        m_file.setTransient(true);

        model.addParameter(m_file);
    }

    protected WoolySession doProcess(final WoolyQuery query) {
        final WoolySession session = new WoolySession(this);

        m_file.set(session, query.getPage());

        return session;
    }

    protected String doRender(final WoolySession session) {
        return (String) m_file.get(session);
    }
}
