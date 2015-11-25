package butyl;

import java.lang.reflect.*;

public final class ReflectFunctions {
    public static Object newInstance(final String sclass) {
        final Class jclass;

        try {
            jclass = Class.forName(sclass);
        } catch (ClassNotFoundException e) {
            throw new IllegalStateException
                ("Class '" + sclass + "' not found");
        }

        return newInstance(jclass);
    }

    public static Object newInstance(final Class jclass) {
        final Object object;

        try {
            object = jclass.newInstance();
        } catch (InstantiationException e) {
            throw new IllegalStateException(e);
        } catch (IllegalAccessException e) {
            throw new IllegalStateException(e);
        }

        return object;
    }
}
