package tuba.util;

import java.util.*;

public final class StringFunctions {
    public static String rfill(String string, final int width) {
        if (string == null) {
            string = "";
        }

        final StringBuilder builder = new StringBuilder();

        builder.append(string);

        if (string.length() < width) {
            final char[] spaces = new char[width - string.length()];
            Arrays.fill(spaces, ' ');

            builder.append(spaces);
        }

        return builder.toString();
    }

    public static String lfill(String string, final int width) {
        if (string == null) {
            string = "";
        }

        final StringBuilder builder = new StringBuilder();

        if (string.length() < width) {
            final char[] spaces = new char[width - string.length()];
            Arrays.fill(spaces, ' ');

            builder.append(spaces);
        }

        builder.append(string);

        return builder.toString();
    }

    public static String repeat(final String string, final int count) {
        final StringBuilder builder = new StringBuilder
            (string.length() * count);

        for (int i = 0; i < count; i++) {
            builder.append(string);
        }

        return builder.toString();
    }

    public static String lcolumn(final String string, final int width) {
        return rfill(string, width).substring(0, width);
    }

    public static String rcolumn(final String string, final int width) {
        return lfill(string, width).substring(0, width);
    }
}
