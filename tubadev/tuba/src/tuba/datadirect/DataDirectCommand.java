package tuba.datadirect;

import java.io.*;
import java.net.*;
import java.util.*;
import tuba.runtime.*;
import tuba.datadirect.xtvd.*;
import tuba.util.*;

final class DataDirectCommand extends Command {
    DataDirectCommand(final TubaCommand parent) {
        super(":datadirect", parent);

        setSummary("Commands for talking to the DataDirect TV " +
                   "listings service");
        setDelegate(new HelpCommand(this));

        new Update(this);
        new Authenticate(this);
        new Fetch(this);
        new Parse(this);
        new Save(this);
    }

    private static class Update extends Command {
        private Update(final Command parent) {
            super("update", parent);
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            final DataDirectSession session = DataDirectModule.getModule
                ().getSession();

            try {
                session.open();

                session.authenticate();
                session.update();
            } finally {
                session.close();
            }
        }
    }

    private static class Authenticate extends Command {
        private Authenticate(final Command parent) {
            super("authenticate", parent);
        }

        private Authenticate(final String name, final Command parent) {
            super(name, parent);
        }

        void run(final CommandArguments args,
                 final PrintWriter err,
                 final DataDirectSession session)
                throws CommandException, IOException {
            session.authenticate();
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            final DataDirectSession session = DataDirectModule.getModule
                ().getSession();

            try {
                session.open();

                run(args, err, session);

                final String auth = session.getAuthorization();

                if (auth == null) {
                    // XXX Try to fail harder here?
                    out.println("Authentication failed");
                } else {
                    out.println("Authentication succeeded");
                    out.println(auth);
                }
            } finally {
                session.close();
            }
        }
    }

    private static class Fetch extends Authenticate {
        private Fetch(final Command parent) {
            super("fetch", parent);
        }

        void run(final CommandArguments args,
                 final PrintWriter out,
                 final PrintWriter err,
                 final DataDirectSession session)
                throws CommandException, IOException {
            super.run(args, err, session);

            final URL url = session.fetch();

            out.println(url);
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            final DataDirectSession session = DataDirectModule.getModule
                ().getSession();

            try {
                session.open();

                run(args, out, err, session);
            } finally {
                session.close();
            }
        }
    }

    private static class Parse extends Command {
        private Parse(final String name, final Command parent) {
            super(name, parent);
        }

        private Parse(final Command parent) {
            this("parse", parent);
        }

        XtvdElement run(final DataDirectSession session,
                        final File file)
                throws CommandException, IOException {
            final URL url = file.toURL();

            return session.parse(url);
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            final String sfile = args.require(0);

            args.check(err);

            final File file = new File(sfile);

            if (!file.exists()) {
                throw new CommandException
                    ("Cannot find file '" + file.getAbsolutePath() + "'");
            }

            final DataDirectSession session = DataDirectModule.getModule
                ().getSession();

            try {
                session.open();

                run(session, file);
            } finally {
                session.close();
            }
        }
    }

    private static class Save extends Parse {
        private Save(final Command parent) {
            super("save", parent);
        }

        XtvdElement run(final DataDirectSession session,
                        final File file)
                throws CommandException, IOException {
            final XtvdElement elem = super.run(session, file);

            session.save(elem);

            return elem;
        }
    }
}
