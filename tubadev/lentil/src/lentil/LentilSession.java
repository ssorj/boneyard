package lentil;

import java.io.*;
import java.sql.*;
import java.util.*;

public class LentilSession extends Session {
    private final String m_url;
    private Connection m_conn;

    public LentilSession(final String name, final String url) {
	super(name);

        m_url = url;
    }

    private String getJdbcUrl() {
        return m_url;
    }

    public final Connection getConnection() {
        return m_conn;
    }

    public void open() {
        try {
            m_conn = DriverManager.getConnection(getJdbcUrl());
        } catch (SQLException e) {
            throw new LentilConnectionException(e);
        }

        try {
            m_conn.setReadOnly(true);
            m_conn.setAutoCommit(false);
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    public final void setWriteEnabled(final boolean enabled) {
        try {
            m_conn.setReadOnly(!enabled);
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    public void close() {
        try {
            if (m_conn != null) m_conn.close();
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }

        m_conn = null;
    }

    public final void commit() {
        try {
            m_conn.commit();
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    public final void rollback() {
        try {
            m_conn.rollback();
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }

    public final void setNewKey(final LentilObject object) {
	object.setNewKey(this);
    }

    public final LentilCursor load(final LentilClass lclass) {
        return lclass.load(this);
    }

    public final void load(final LentilObject object,
			   final LentilCursor cursor) {
	object.load(cursor);
    }

    public final void load(final LentilObject object,
			   final Object key) throws LentilObjectNotFound {
        object.setKey(key);
        object.load(this, object.getLentilClass().getLoadSql(object));
    }

    public final void load(final LentilObject object,
			   final String sfield,
			   final Object value) throws LentilObjectNotFound {
        final LentilClass lclass = object.getLentilClass();
        final LentilField field = lclass.getField(sfield);

        if (field == null) throw new IllegalStateException();

        field.set(object, value);

        final StringBuilder builder = new StringBuilder();

        builder.append(lclass.getLoadSql());
        builder.append(" where ");
        builder.append(field.getColumn());
        builder.append(" = ");
        builder.append(field.getSqlLiteral(object));

        object.load(this, builder.toString());
    }

    public final void save(final LentilObject object) {
	object.save(this);
    }

    public final int update(final LentilObject object) {
	return object.update(this);
    }

    public final int insert(final LentilObject object) {
	return object.insert(this);
    }

    public final int delete(final LentilObject object) {
	return object.delete(this);
    }

    public final int delete(final LentilClass lclass) {
        return lclass.delete(this);
    }

    public final LentilCursor read(final String sql) {
        final ResultSet results;

        try {
            final Statement stmt = getConnection().createStatement();

            stmt.execute(sql);

            results = stmt.getResultSet();
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }

        return new LentilCursor(results);
    }

    public final int write(final String sql) {
        final int count;

        try {
            final Statement stmt = getConnection().createStatement();
            stmt.execute(sql);

            count = stmt.getUpdateCount();

            stmt.close();
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }

        return count;
    }
}
