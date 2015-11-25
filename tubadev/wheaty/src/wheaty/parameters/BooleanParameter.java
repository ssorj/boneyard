package wheaty.parameters;

import wheaty.*;

public final class BooleanParameter extends ScalarParameter {
    public BooleanParameter(final String name) {
        super(name);
    }

    protected String doScalarMarshal(final Object object) throws Exception {
        return ((Boolean) object).toString();
    }

    protected Object doScalarUnmarshal(final String string) throws Exception {
        return new Boolean(string);
    }

    protected Object doScalarCopy(final Object orig) {
        return new Boolean(((Boolean) orig).booleanValue());
    }
}
