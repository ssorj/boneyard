package tuba.runtime;

import java.io.*;
import java.math.*;
import java.util.*;
import lentil.*;
import org.jdom.*;
import org.jdom.output.*;
import tuba.runtime.model.*;
import tuba.util.*;

final class RequestCommands {
    static void add(final TubaCommand parent) {
        new RequestProgram(parent);
        new RequestSeries(parent);
        new RequestStation(parent);
    }

    private static class RequestSeries extends Command {
        private RequestSeries(final Command parent) {
            super("request-series", parent);

            setParameterSyntax("SERIES-KEY [PRIORITY]");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            args.require(0);

            args.check(err);

            final Long seriesKey = args.getLong(0);
            final Integer priority = args.getInteger(1, new Integer(0));

            args.check(err);

            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();

                final Series series = new Series();

                try {
                    conn.load(series, seriesKey);
                } catch (LentilObjectNotFound e) {
                    throw new CommandException
                        ("Series " + seriesKey + " not found");
                }

                series.Priority = priority;

                conn.setWriteEnabled(true);
                conn.save(series);
                conn.commit();
            } finally {
                conn.close();
            }
        }
    }

    private static class RequestStation extends Command {
        private RequestStation(final Command parent) {
            super("request-station", parent);

            setParameterSyntax("STATION-KEY [PRIORITY]");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            args.require(0);

            args.check(err);

            final Long stationKey = args.getLong(0);
            final Integer priority = args.getInteger(1, new Integer(0));

            args.check(err);

            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();

                final Station station = new Station();

                try {
                    conn.load(station, stationKey);
                } catch (LentilObjectNotFound e) {
                    throw new CommandException
                        ("Station " + stationKey + " not found");
                }

                station.Priority = priority;

                conn.setWriteEnabled(true);
                conn.save(station);
                conn.commit();
            } finally {
                conn.close();
            }
        }
    }

    private static class RequestProgram extends Command {
        private RequestProgram(final Command parent) {
            super("request-program", parent);

            setParameterSyntax("PROGRAM-KEY [PRIORITY]");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            args.require(0);

            args.check(err);

            final Long programKey = args.getLong(0);
            final Integer priority = args.getInteger(1, new Integer(0));

            args.check(err);

            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();

                final Program program = new Program();

                try {
                    conn.load(program, programKey);
                } catch (LentilObjectNotFound e) {
                    throw new CommandException
                        ("Program " + programKey + " not found");
                }

                program.Priority = priority;

                conn.setWriteEnabled(true);
                conn.save(program);
                conn.commit();
            } finally {
                conn.close();
            }
        }
    }
}
