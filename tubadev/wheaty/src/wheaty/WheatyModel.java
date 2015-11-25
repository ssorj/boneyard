package wheaty;

import java.util.*;

public class WheatyModel {
    private final String m_name;
    private final Map<String, WheatyParameter> m_params;

    public WheatyModel(final String name) {
        m_name = name;
        m_params = new HashMap();
    }

    public final String getName() {
        return m_name;
    }

    public final void addParameter(final WheatyParameter param) {
        param.setModel(this);
        m_params.put(param.getPath(), param);
    }

    public final WheatyParameter getParameter(final String key) {
        return m_params.get(key);
    }

    final public Collection<WheatyParameter> getParameters() {
        return m_params.values();
    }

    public final void unmarshal(final WheatyDocument doc,
                                final WheatySession session) {
        for (final WheatyParameter param : getParameters()) {
            final WheatyValue parent = doc.getValue(getName());

            if (parent != null) {
                final WheatyValue value = parent.getChild(param.getPath());

                if (value != null) {
                    final Object object = param.unmarshal(value);

                    session.set(param, object);
                }
            }
        }
    }

    public final void marshal(final WheatySession session,
                              final WheatyDocument doc) {
        for (final WheatyParameter param : getParameters()) {
            if (session.isSet(param)) {
                final Object object = session.get(param);

                System.out.println("object=" + object);

                final WheatyValue value = param.marshal(object);

                // XXX doc.lock();

                WheatyValue parent = doc.getValue(getName());

                if (parent == null) {
                    parent = new WheatyValue(getName());
                    doc.addValue(parent);
                }

                parent.addChild(value);

                // XXX doc.unlock();
            }
        }
    }
}