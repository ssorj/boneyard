package wheaty;

import java.util.*;

public abstract class WheatyParameter {
    private final String m_name;
    private WheatyParameter m_parent;
    private final Map<String, WheatyParameter> m_children;
    private WheatyModel m_model;
    private boolean m_transient;
    private boolean m_nullable;
    private Object m_value;

    protected WheatyParameter(final String name) {
        if (name == null) throw new IllegalArgumentException();

        m_name = name;
        m_children = new LinkedHashMap();
        m_transient = false;
        m_nullable = true;
    }

    private Map<String, WheatyParameter> getChildMap() {
        return m_children;
    }

    public final String getName() {
        return m_name;
    }

    public final WheatyParameter getParent() {
        return m_parent;
    }

    private void setParent(final WheatyParameter parent) {
        if (parent == null) throw new IllegalArgumentException();
        if (m_parent != null) throw new IllegalStateException();

        m_parent = parent;
    }

    public final Collection<WheatyParameter> getChildren() {
        return getChildMap().values();
    }

    public final WheatyParameter getChild(final String name) {
        return getChildMap().get(name);
    }

    public final void addChild(final WheatyParameter param) {
        getChildMap().put(param.getName(), param);
        param.setParent(this);
    }

    public final WheatyModel getModel() {
        return m_model;
    }

    void setModel(final WheatyModel model) {
        m_model = model;
    }

    public final String getPath() {
        final String path;

        if (getParent() == null) {
            path = getName();
        } else {
            path = getParent().getPath() + "." + getName();
        }

        return path;
    }

    public final boolean isTransient() {
        return m_transient;
    }

    public final void setTransient(final boolean transient_) {
        m_transient = transient_;
    }

    public final boolean isNullable() {
        return m_nullable;
    }

    public final void setNullable(final boolean nullable) {
        m_nullable = nullable;
    }

    public final Object get() {
        return m_value;
    }

    public final void set(final Object value) {
        m_value = value;
    }

    public final Object get(final WheatySession session) {
        if (session == null) throw new IllegalArgumentException();

        Object object = session.get(this);

        if (object == null) {
            object = get();
        }

        return object;
    }

    public final boolean isSet(final WheatySession session) {
        return session.isSet(this);
    }

    public final void set(final WheatySession session, final Object object) {
        if (session == null) throw new IllegalArgumentException();

        if (object == null && !isNullable()) {
            throw new IllegalArgumentException
                ("Parameter " + getPath() + " cannot be set to null");
        }

        session.set(this, object);
    }

    public final Object unmarshal(final WheatyValue value) {
        if (value == null) throw new IllegalArgumentException("value");

        return doUnmarshal(value);
    }

    protected abstract Object doUnmarshal(final WheatyValue value);

    public final WheatyValue marshal(final Object object) {
        final WheatyValue value = new WheatyValue(getName());

        if (object != null) {
            doMarshal(object, value);
        }

        return value;
    }

    protected abstract void doMarshal(final Object object,
                                      final WheatyValue value);

    public final Object copy(final Object object) {
        return doCopy(object);
    }

    protected abstract Object doCopy(final Object object);

    public final void print() {
        System.out.print(getClass().getName() + "@" + getPath());

        for (final WheatyParameter child : getChildren()) {
            child.print();
        }
    }
}
