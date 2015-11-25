package butyl;

import java.util.*;

public final class DebugFunctions {
    public static void print(final String name, final Map map) {
        System.out.println(name + " = {");

        for (final Object value : map.values()) {
            System.out.println("  " + value);
        }

        System.out.println("}");
    }
}
