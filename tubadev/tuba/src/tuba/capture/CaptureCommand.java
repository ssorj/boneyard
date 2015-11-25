package tuba.capture;

import java.io.*;
import java.util.*;
import tuba.runtime.*;
import tuba.util.*;

class CaptureCommand extends Command {
    CaptureCommand(final TubaCommand parent) {
        super(":capture", parent);

        setSummary("Commands for capturing TV programs");
        setDelegate(new HelpCommand(this));

        new Schedule(this);
    }

    private static class Schedule extends Command {
        private Schedule(final Command parent) {
            super("schedule", parent);

            setSummary
                ("Find desired showings, resolve winners, and schedule them");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            final CaptureSession session = CaptureModule.get().getSession();

            try {
                session.open();

                session.load();
                session.resolve();
                session.schedule();
            } finally {
                session.close();
            }
        }
    }
}
