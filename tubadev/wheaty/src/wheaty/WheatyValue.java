package wheaty;

import java.util.*;

public final class WheatyValue {
    private final String m_name;
    private WheatyValue m_parent;
    private final Map<String, WheatyValue> m_children;

    private String m_value;

    public WheatyValue(final String name) {
        if (name == null) throw new IllegalArgumentException();
        if (name.equals("")) throw new IllegalArgumentException();
        if (name.indexOf('.') != -1) throw new IllegalArgumentException();

        m_name = name;
        m_children = new LinkedHashMap();
    }

    private Map<String, WheatyValue> getChildMap() {
        return m_children;
    }

    public String getName() {
        return m_name;
    }

    public WheatyValue getParent() {
        return m_parent;
    }

    private void setParent(final WheatyValue parent) {
        m_parent = parent;
    }

    public Collection<WheatyValue> getChildren() {
        return getChildMap().values();
    }

    public String get() {
        return m_value;
    }

    public void set(final String value) {
        m_value = value;
    }

    public String getPath() {
        final String path;

        if (getParent() == null) {
            path = getName();
        } else {
            path = getParent().getPath() + "." + getName();
        }

        return path;
    }

    public WheatyValue getChild(final String name) {
        return getChildMap().get(name);
    }

    public void addChild(final WheatyValue value) {
        getChildMap().put(value.getName(), value);
        value.setParent(this);
    }

    public void traverse(final Visitor visitor) {
        for (final WheatyValue child : getChildren()) {
            child.traverse(visitor);
        }

        visitor.visit(this);
    }

    public static interface Visitor {
        void visit(final WheatyValue value);
    }

    public void print() {
        System.out.print(getPath());
        System.out.print(" = ");
        System.out.print(get());
        System.out.println();

        for (final WheatyValue value : getChildren()) {
            value.print();
        }
    }

    public String toString() {
        return "[" + getPath() + "=" + get() + "]";
    }
}
