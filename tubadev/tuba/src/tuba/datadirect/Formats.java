package tuba.datadirect;

import java.text.*;
import java.util.*;

final class Formats {
    private static final DateFormat s_time = new SimpleDateFormat
        ("yyyy-MM-dd'T'HH:mm:ss'Z'");

    private static final DateFormat s_date = new SimpleDateFormat
        ("yyyy-MM-dd");

    static {
        s_time.setTimeZone(TimeZone.getTimeZone("UTC"));
    }

    static Date parseTime(final String timestamp) {
        final Date time;

        try {
            time = s_time.parse(timestamp);
        } catch (ParseException e) {
            throw new IllegalArgumentException(e);
        }

        return time;
    }

    static String formatTime(final Date time) {
        return s_time.format(time);
    }

    static Date parseDate(final String datestamp) {
        final Date date;

        try {
            date = s_date.parse(datestamp);
        } catch (ParseException e) {
            throw new IllegalArgumentException(e);
        }

        return date;
    }

    static long parseDuration(final String duration) {
        final int hours = Integer.parseInt(duration.substring(2, 4));
        final int minutes = Integer.parseInt(duration.substring(5, 7));

        return ((hours * 60) + minutes) * 60 * 1000;
    }
}
