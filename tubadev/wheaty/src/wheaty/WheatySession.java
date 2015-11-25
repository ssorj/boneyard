package wheaty;

import java.util.*;

public class WheatySession {
    private final Map<WheatyParameter, Object> m_objects;
    private final WheatySession m_trunk;

    protected WheatySession() {
        m_objects = new HashMap();
        m_trunk = null;
    }

    protected WheatySession(final WheatySession trunk) {
        m_objects = new HashMap();
        m_trunk = trunk;
    }

    private final Map<WheatyParameter, Object> getObjects() {
        return m_objects;
    }

    private final WheatySession getTrunk() {
        return m_trunk;
    }

    protected final Object get(final WheatyParameter param) {
        if (param == null) throw new IllegalArgumentException();

        Object object = getObjects().get(param);

        if (object == null && getTrunk() != null) {
            object = getTrunk().get(param);
        }

        return object;
    }

    protected final void set(final WheatyParameter param,
                             final Object object) {
        if (param == null) throw new IllegalArgumentException();

        getObjects().put(param, object);
    }

    protected final boolean isSet(final WheatyParameter param) {
        if (param == null) throw new IllegalArgumentException();

        return getObjects().containsKey(param);
    }

    public void print() {
        System.out.println("objects=" + m_objects);
        System.out.println("trunk=" + m_trunk);
    }
}
