package tuba.util;

import java.sql.*;

public final class JdbcFunctions {
    public static void print(final ResultSet results) {
        try {
            final ResultSetMetaData md = results.getMetaData();

            for (int i = 1; i <= md.getColumnCount(); i++) {
                System.out.println("column " + md.getColumnName(i));
            }
        } catch (SQLException e) {
            throw new IllegalStateException(e);
        }
    }
}
