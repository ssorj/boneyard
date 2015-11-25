package tuba.runtime;

import java.io.*;
import java.util.*;
import lentil.*;
import tuba.util.*;

public final class TubaConnection extends LentilSession {
    TubaConnection(final String url) {
        super("data", url);
    }

    public LentilCursor load(final Class jclass) {
	return load(RuntimeModule.getModule().getLentilClass(jclass));
    }

    public int delete(final Class jclass) {
        return delete(RuntimeModule.getModule().getLentilClass(jclass));
    }
}
