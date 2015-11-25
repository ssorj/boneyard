package wooly;

import java.util.*;
import wheaty.*;

public final class SessionLocal extends WheatyParameter {
    public SessionLocal(final String name) {
        super(name);

        setTransient(true);
    }

    protected Object doUnmarshal(final WheatyValue value) {
        throw new IllegalStateException();
    }

    protected void doMarshal(final Object object,
                             final WheatyValue value) {
        throw new IllegalStateException();
    }

    protected Object doCopy(final Object object) {
        throw new IllegalStateException();
    }
}
