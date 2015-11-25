package wheaty;

import java.util.*;

public class WheatyDocument {
    private final WheatyValue m_root;

    public WheatyDocument() {
        m_root = new WheatyValue("root");
    }

    private WheatyValue getRootValue() {
        return m_root;
    }

    public WheatyValue getValue(final String key) {
        return getRootValue().getChild(key);
    }

    public void addValue(final WheatyValue value) {
        getRootValue().addChild(value);
    }

    public Collection<WheatyValue> getValues() {
        return getRootValue().getChildren();
    }

    public void print() {
        System.out.println(WheatyDocument.class.getName());

        getRootValue().print();
    }
}
