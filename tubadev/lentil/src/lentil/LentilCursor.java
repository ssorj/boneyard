package lentil;

import java.sql.*;
import java.util.*;

public final class LentilCursor {
    private final ResultSet m_results;

    LentilCursor(final ResultSet results) {
        m_results = results;
    }

    public ResultSet getResultSet() {
        return m_results;
    }

    public boolean next() {
        final boolean next;

        try {
            next = getResultSet().next();
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }

        return next;
    }

    public Object getObject(final String name) {
        final Object object;

        try {
            object = getResultSet().getObject(name);
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }

        return object;
    }

    public Object getObject(final int index) {
        final Object object;

        try {
            object = getResultSet().getObject(index);
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }

        return object;
    }

    public void close() {
        try {
            getResultSet().close();
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }
}
