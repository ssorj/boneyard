package tuba.dvb;

import java.io.*;
import java.util.*;
import tuba.runtime.*;
import tuba.capture.*;
import tuba.util.*;

final class DvbCommand extends Command {
    DvbCommand(final Command parent) {
        super(":dvb", parent);

        setSummary("Commands for using a Linux DVB capture device");
        setDelegate(new HelpCommand(this));

        new Capture(this);
        new PrintChannels(this);
    }

    private static class Capture extends Command {
        Capture(final Command parent) {
            super("capture", parent);

            setParameterSyntax("CHANNEL FILE DURATION");
            setSummary("Capture CHANNEL to FILE for DURATION seconds");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            args.require(0);
            args.require(1);
            args.require(2);

            args.check(err);

            final String schan = args.get(0);
            final String sfile = args.get(1);
            final Integer duration = args.getInteger(2);

            args.check(err);

            final Channel chan = DvbModule.getModule().getChannels().get
                (schan);

            if (chan == null) {
                throw new CommandException
                    ("Channel '" + args.get(0) + "' not found");
            }

            final File file = new File(sfile);

            if (duration.intValue() < 0) {
                throw new CommandException
                    ("The duration cannot be negative");
            }

            final long now = System.currentTimeMillis();
            final Date end = new Date(now + duration.intValue() * 1000);

            DvbModule.getModule().getTuner().capture(chan, file, end);
        }
    }

    private static class PrintChannels extends Command {
        PrintChannels(final Command parent) {
            super("print-channels", parent);

            setSummary("List all of the loaded channels");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            final Iterator channels = DvbModule.getModule().getChannels
                ().iterator();

            while (channels.hasNext()) {
                final Channel channel = (Channel) channels.next();

                channel.print(out);
            }
        }
    }
}
