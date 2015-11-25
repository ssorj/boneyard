package tuba.util;

import java.io.*;
import java.util.*;

public final class TablePrinter {
    private final PrintWriter m_out;
    private final List m_columns;

    public TablePrinter(final PrintWriter out) {
        m_out = out;
        m_columns = new ArrayList();
    }

    public void column(final String title,
                       final int width,
                       final String flags) {
        final Column column = new Column();

        column.Title = title;
        column.Width = width;
        column.Flags = flags;

        m_columns.add(column);
    }

    public void print(final String string) {
        m_out.print(string);
    }

    public void println() {
        m_out.println();
    }

    public void printHeader() {
        final int len = m_columns.size();

        for (int i = 0; i < len; i++) {
            final Column column = (Column) m_columns.get(i);

            printColumn(column, column.Title);

            if (i < len -1) {
                print("  ");
            }
        }

        println();

        for (int i = 0; i < len; i++) {
            final Column column = (Column) m_columns.get(i);
            final char[] dashes = new char[column.Width];
            Arrays.fill(dashes, '-');

            m_out.print(dashes);

            if (i < len -1) {
                print("  ");
            }
        }

        println();
    }

    public void printRow(final Object[] values) {
        final int len = values.length;

        for (int i = 0; i < len; i++) {
            final Column column = (Column) m_columns.get(i);
            final Object value = values[i];

            printColumn(column, value);

            if (i < len - 1) {
                print("  ");
            }
        }

        println();
    }

    private void printColumn(final Column column, Object value) {
        if (value == null) {
            value = column.Default;
        }

        if (column.Flags.indexOf('r') != -1) {
            print(StringFunctions.rcolumn(value.toString(), column.Width));

            return;
        }

        print(StringFunctions.lcolumn(value.toString(), column.Width));
    }

    private class Column {
        public String Title;
        public int Width;
        public String Flags;
        public String Default = "-";
    }
}
