package lentil;

import butyl.*;
import java.io.*;
import java.lang.reflect.*;
import java.util.*;

public final class LentilClass {
    private final Class m_jclass;
    private final LentilPackage m_lpackage;
    private final Map m_lfields;
    private String m_table;
    private String m_sequence;
    private LentilField m_key;

    LentilClass(final Class jclass, final LentilPackage lpackage) {
        m_jclass = jclass;
        m_lpackage = lpackage;
        m_lfields = new LinkedHashMap();

        getLentilPackage().getClasses().put(jclass, this);
    }

    Class getJavaClass() {
        return m_jclass;
    }

    LentilPackage getLentilPackage() {
        return m_lpackage;
    }

    String getTable() {
        return m_table;
    }

    void setTable(final String table) {
        m_table = table;
    }

    LentilField getKeyField() {
        return m_key;
    }

    void setKeyField(final LentilField key) {
        m_key = key;
    }

    String getKeySequence() {
        return m_sequence;
    }

    void setKeySequence(final String sequence) {
        m_sequence = sequence;
    }

    Map getFields() {
        return m_lfields;
    }

    public LentilField getField(final String jname) {
        return (LentilField) getFields().get(jname);
    }

    LentilObject newObject(final LentilSession session) {
        return (LentilObject) ReflectFunctions.newInstance(getJavaClass());
    }

    Object newKey(final LentilSession session) {
        final Object key;
        LentilCursor cursor = null;

        try {
            cursor = session.read(getNewKeySql());

            if (cursor.next()) {
                key = cursor.getObject(1);
            } else {
                throw new IllegalStateException();
            }
        } finally {
            if (cursor != null) cursor.close();
        }

        return key;
    }

    LentilCursor load(final LentilSession session) {
        return session.read(getLoadSql());
    }

    int delete(final LentilSession session) {
        return session.write(getDeleteSql());
    }

    private String getNewKeySql() {
        if (getKeyField() == null) throw new IllegalStateException();

        return "call next value for " + getKeySequence();
    }

    String getLoadSql() {
        if (getFields().isEmpty()) throw new IllegalStateException();

        final StringBuilder builder = new StringBuilder();

        builder.append("select " + getColumnList() + " ");
        builder.append("from " + getTable());

        return builder.toString();
    }

    String getLoadSql(final LentilObject object) {
        return getLoadSql() + " " + getWhereClause(object);
    }

    String getInsertSql(final LentilObject object) {
        if (getFields().isEmpty()) throw new IllegalStateException();

        final StringBuilder builder = new StringBuilder();

        builder.append("insert into " + getTable() + " (");
        builder.append(getColumnList());
        builder.append(") values (");

        final Iterator iter = getFields().values().iterator();

        while (iter.hasNext()) {
            final LentilField field = (LentilField) iter.next();

            builder.append(field.getSqlLiteral(object));
            builder.append(", ");
        }

        builder.delete(builder.length() - 2, builder.length());
        builder.append(")");

        return builder.toString();
    }

    String getUpdateSql(final LentilObject object) {
        if (getFields().isEmpty()) throw new IllegalStateException();
        if (getKeyField() == null) throw new IllegalStateException();

        final StringBuilder builder = new StringBuilder();

        builder.append("update " + getTable() + " ");
        builder.append("set ");

        final Iterator iter = getFields().values().iterator();

        while (iter.hasNext()) {
            final LentilField field = (LentilField) iter.next();

            builder.append(field.getColumn());
            builder.append(" = ");
            builder.append(field.getSqlLiteral(object));
            builder.append(", ");
        }

        builder.delete(builder.length() - 2, builder.length());
        builder.append(" ");
        builder.append(getWhereClause(object));

        return builder.toString();
    }

    String getDeleteSql() {
        return "delete from " + getTable();
    }

    String getDeleteSql(final LentilObject object) {
        return getDeleteSql() + " " + getWhereClause(object);
    }

    private String getColumnList() {
        final StringBuilder builder = new StringBuilder();

        final Iterator iter = getFields().values().iterator();

        while (iter.hasNext()) {
            final LentilField field = (LentilField) iter.next();

            builder.append(field.getColumn());
            builder.append(", ");
        }

        builder.delete(builder.length() - 2, builder.length());

        return builder.toString();
    }

    private String getWhereClause(final LentilObject object) {
        if (getKeyField() == null) throw new IllegalStateException();

        final String key = getKeyField().getSqlLiteral(object);

        return "where " + getKeyField().getColumn() + " = " + key;
    }

    Field getJavaField(final String name) {
        final Field jfield;

        try {
            jfield = getJavaClass().getField(name);
        } catch (NoSuchFieldException e) {
            throw new IllegalStateException(e);
        } catch (SecurityException e) {
            throw new IllegalStateException(e);
        }

        return jfield;
    }

    public final void print(final PrintWriter out) {
        out.print("class " + getJavaClass().getName() + " ");
        out.println(getTable() + " {");

        final Iterator iter = getFields().values().iterator();

        while (iter.hasNext()) {
            ((LentilField) iter.next()).print(out);
        }

        if (getKeyField() != null) {
            out.println();
            out.print("    key " + getKeyField().getName() + " ");
            out.println(getKeySequence() + ";");
        }

        out.println("}");
    }
}
