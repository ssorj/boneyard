package lentil;

import java.io.*;
import java.lang.reflect.*;
import java.util.*;

public class LentilField {
    private final Field m_jfield;
    private final LentilClass m_lclass;
    private String m_column;

    LentilField(final Field jfield, final LentilClass lclass) {
        m_jfield = jfield;
        m_lclass = lclass;

        getLentilClass().getFields().put(getName(), this);
    }

    Field getJavaField() {
        return m_jfield;
    }

    public String getName() {
        return getJavaField().getName();
    }

    public LentilClass getLentilClass() {
        return m_lclass;
    }

    String getColumn() {
        return m_column;
    }

    void setColumn(final String column) {
        m_column = column;
    }

    public Object get(final Object object) {
        final Object value;

        try {
            value = getJavaField().get(object);
        } catch (IllegalAccessException e) {
            throw new IllegalStateException(e);
        }

        return value;
    }

    public void set(final Object object, Object value) {
        //System.out.println(getLentilClass().getJavaClass() + " " + getName());
        //System.out.println("  object " + object);
        //System.out.println("  value " + value);

        try {
            getJavaField().set(object, value);
        } catch (IllegalAccessException e) {
            throw new IllegalStateException(e);
        }
    }

    Object get(final LentilCursor cursor) {
        Object object = cursor.getObject(getColumn());

        if (getJavaField().getType().equals(Date.class)) {
            if (object instanceof Long) {
                object = new Date(((Long) object).longValue());
            }
        }

        return object;
    }

    String getSqlLiteral(final Object object) {
        final Object value = get(object);
        final String string;

        if (value == null) {
            string = "null";
        } else if (value instanceof Date) {
            string = String.valueOf(((Date) value).getTime());
        } else if (value instanceof String) {
            string = "'" + ((String) value).replaceAll("'", "''") + "'";
        } else if (value instanceof Number) {
            string = value.toString();
        } else if (value instanceof Boolean) {
            string = value.toString();
        } else {
            throw new IllegalStateException();
        }

        return string;
    }

    public final void print(final PrintWriter out) {
        out.println("    field " + getName() + " " + getColumn() + ";");
    }
}
