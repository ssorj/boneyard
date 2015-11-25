package wheaty.parameters;

import wheaty.*;

public abstract class ScalarParameter extends WheatyParameter {
    protected ScalarParameter(final String name) {
        super(name);
    }

    protected final Object doUnmarshal(final WheatyValue value) {
        final String string = value.get();
        final Object object;

        if (string == null) {
            object = null;
        } else {
            try {
                object = doScalarUnmarshal(value.get());
            } catch (final Exception e) {
                throw new IllegalStateException(e);
            }
        }

        return object;
    }

    protected final void doMarshal(final Object object,
                                   final WheatyValue value) {
        final String string;

        try {
            string = doScalarMarshal(object);
        } catch (final Exception e) {
            throw new IllegalStateException(e);
        }

        value.set(string);
    }

    protected final Object doCopy(final Object object) {
        final Object copy;

        if (object == null) {
            copy = null;
        } else {
            try {
                copy = doScalarCopy(object);
            } catch (final Exception e) {
                throw new IllegalStateException(e);
            }
        }

        return copy;
    }

    protected abstract Object doScalarUnmarshal(final String string)
        throws Exception;

    protected abstract String doScalarMarshal(final Object object)
        throws Exception;

    protected abstract Object doScalarCopy(final Object object)
        throws Exception;
}
