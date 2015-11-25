package wheaty.documents;

import java.util.*;
import wheaty.*;

public class PropertiesDocument extends WheatyDocument {
    public PropertiesDocument() {
        super();
    }

    public void load(final Properties props) {
        if (props == null) throw new IllegalArgumentException();

        for (final Map.Entry entry : props.entrySet()) {
            final String path = (String) entry.getKey();
            final String[] names = path.split("\\.");
            WheatyValue parent = null;

            for (final String name : names) {
                final WheatyValue child = new WheatyValue(name);

                if (parent == null) {
                    addValue(child);
                } else {
                    parent.addChild(child);
                }

                parent = child;
            }

            parent.set((String) entry.getValue());
        }
    }

    public void save(final Properties props) {
        if (props == null) throw new IllegalArgumentException();

        for (final WheatyValue value : getValues()) {
            value.traverse(new WheatyValue.Visitor() {
                    public void visit(final WheatyValue v) {
                        System.out.println(v.getPath());

                        if (v.get() != null) {
                            props.setProperty(v.getPath(), v.get());
                        }
                    }
                });
        }
    }
}
