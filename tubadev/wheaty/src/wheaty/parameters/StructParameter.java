package wheaty.parameters;

import java.util.*;
import wheaty.*;

public class StructParameter extends WheatyParameter {
    public StructParameter(final String name) {
        super(name);
    }

    protected Object doUnmarshal(final WheatyValue value) {
        final Map map = new LinkedHashMap();

        for (final WheatyParameter param : getChildren()) {
            final String name = param.getName();
            final WheatyValue child = value.getChild(name);

            if (child != null) {
                map.put(name, param.unmarshal(child));
            }
        }

        return map;
    }

    protected void doMarshal(final Object object,
                             final WheatyValue value) {
        final Map map = (Map) object;

        for (final WheatyParameter param : getChildren()) {
            final String name = param.getName();
            final Object child = map.get(name);

            if (child != null) {
                value.addChild(param.marshal(child));
            }
        }
    }

    protected Object doCopy(final Object object) {
        final Map map = (Map) object;
        final Map copy = new LinkedHashMap();

        for (final WheatyParameter param : getChildren()) {
            final String name = param.getName();
            final Object child = map.get(name);

            if (child != null) {
                copy.put(name, param.copy(child));
            }
        }

        return copy;
    }
}
