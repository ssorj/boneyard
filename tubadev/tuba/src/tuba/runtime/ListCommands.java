package tuba.runtime;

import java.io.*;
import java.util.*;
import lentil.*;
import org.jdom.*;
import org.jdom.output.*;
import tuba.runtime.model.*;
import tuba.util.*;

final class ListCommands {
    static void add(final TubaCommand parent) {
        new ListPrograms(parent);
        new ListRecordings(parent);
        new ListSeries(parent);
        new ListStations(parent);
    }

    private static boolean promptContinue(final BufferedReader in,
                                          final PrintWriter out)
            throws IOException {
        out.println();
        out.print("ENTER to continue, 'q' and ENTER to stop: ");
        out.flush();

        final String line = in.readLine();

        if (line != null && line.trim().equals("q")) {
            return true;
        } else {
            return false;
        }
    }

    private static class ListStations extends Command {
        private ListStations(final Command parent) {
            super("list-stations", parent);

            //addAlias("stations");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err) throws IOException {
            final TablePrinter table = new TablePrinter(out);
            table.column("Key", 6, "r");
            table.column("Call Sign", 9, "l");
            table.column("Format", 8, "l");
            table.column("Prio", 4, "r");

            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();

                final LentilCursor cursor = conn.load(Station.class);

                for (int i = 0; cursor.next(); i++) {
                    if (i % 20 == 0) {
                        if (i != 0 && promptContinue(in, out)) {
                            break;
                        }

                        table.printHeader();
                    }

                    final Station station = new Station();
		    conn.load(station, cursor);

                    final Object[] values = new Object[] {
                        station.Key,
                        station.CallSign,
                        station.TransportFormat,
                        station.Priority
                    };

                    table.printRow(values);
                }

		cursor.close();
            } finally {
                conn.close();
            }
        }
    }

    private static class ListSeries extends Command {
        private ListSeries(final Command parent) {
            super("list-series", parent);

            //addAlias("series");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err) throws IOException {
            final TablePrinter table = new TablePrinter(out);
            table.column("Key", 6, "r");
            table.column("Title", 60, "l");
            table.column("Prio", 4, "r");

            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();

                final LentilCursor cursor = conn.load(Series.class);

                for (int i = 0; cursor.next(); i++) {
                    if (i % 20 == 0) {
                        if (i != 0 && promptContinue(in, out)) {
                            break;
                        }

                        table.printHeader();
                    }

                    final Series series = new Series();
		    conn.load(series, cursor);

                    final Object[] values = new Object[] {
                        series.Key,
                        series.Title,
                        series.Priority
                    };

                    table.printRow(values);
                }

		cursor.close();
            } finally {
                conn.close();
            }
        }
    }

    private static class ListPrograms extends Command {
        private ListPrograms(final Command parent) {
            super("list-programs", parent);

            //addAlias("programs");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err) throws IOException {
            final TablePrinter table = new TablePrinter(out);
            table.column("Key", 6, "r");
            table.column("Title", 24, "l");
            table.column("Subtitle", 28, "l");
            table.column("Orig Aired", 10, "l");
            table.column("Prio", 4, "r");

            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();

                final LentilCursor cursor = conn.load(Program.class);

                for (int i = 0; cursor.next(); i++) {
                    if (i % 20 == 0) {
                        if (i != 0 && promptContinue(in, out)) {
                            break;
                        }

                        table.printHeader();
                    }

                    final Program prog = new Program();
		    conn.load(prog, cursor);

                    String date = null;

                    if (prog.OriginalAirDate != null) {
                        date = Tuba.getDateFormat().format
                            (prog.OriginalAirDate);
                    }

                    final Object[] values = new Object[] {
                        prog.Key,
                        prog.Title,
                        prog.Subtitle,
                        date,
                        prog.Priority
                    };

                    table.printRow(values);
                }

		cursor.close();
            } finally {
                conn.close();
            }
        }
    }

    private static class ListRecordings extends Command {
        private ListRecordings(final Command parent) {
            super("list-recordings", parent);

            //addAlias("recordings");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err) throws IOException {
            final TablePrinter table = new TablePrinter(out);
            table.column("Key", 6, "r");
            table.column("Title", 24, "l");
            table.column("Subtitle/Orig Aired", 28, "l");

            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();

                final LentilCursor cursor = conn.load(Recording.class);

                for (int i = 0; cursor.next(); i++) {
                    if (i % 20 == 0) {
                        if (i != 0 && promptContinue(in, out)) {
                            break;
                        }

                        table.printHeader();
                    }

                    final Recording rec = new Recording();
		    conn.load(rec, cursor);

                    String subtitle = rec.Subtitle;

                    if (subtitle == null && rec.OriginalAirDate != null) {
                        subtitle = Tuba.getDateFormat().format
                            (rec.OriginalAirDate);
                    }

                    final Object[] values = new Object[] {
                        rec.Key,
                        rec.Title,
                        subtitle,
                    };

                    table.printRow(values);
                }

		cursor.close();
            } finally {
                conn.close();
            }
        }
    }
}
