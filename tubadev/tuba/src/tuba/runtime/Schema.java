package tuba.runtime;

import tuba.util.*;

public final class Schema {
    public static final StringCatalog s_sql = new StringCatalog
        (Schema.class, "Schema.sql");

    Schema() {
    }

    public void create(final TubaConnection conn) {
        conn.write(s_sql.get("create"));
    }

    public void drop(final TubaConnection conn) {
        conn.write(s_sql.get("drop"));
    }
}
