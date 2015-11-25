package wheaty.parameters;

import wheaty.*;

public final class StringParameter extends ScalarParameter {
    public StringParameter(final String name) {
        super(name);
    }

    protected String doScalarMarshal(final Object object) throws Exception {
        return object.toString();
    }

    protected Object doScalarUnmarshal(final String string) throws Exception {
        return string;
    }

    protected Object doScalarCopy(final Object orig) {
        return new String((String) orig);
    }
}
