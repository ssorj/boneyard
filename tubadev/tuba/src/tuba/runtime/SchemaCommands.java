package tuba.runtime;

import java.io.*;
import java.util.*;
import lentil.*;
import org.jdom.*;
import org.jdom.output.*;
import tuba.runtime.model.*;
import tuba.util.*;

final class SchemaCommands {
    static void add(final TubaCommand parent) {
        new CreateSchema(parent);
        new DropSchema(parent);
    }

    private static class CreateSchema extends Command {
        private CreateSchema(final Command parent) {
            super("create-schema", parent);

            setSummary("Create database objects (tables, indexes, etc.)");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();
                conn.setWriteEnabled(true);

                RuntimeModule.getModule().getSchema().create(conn);

                conn.commit();
            } finally {
                conn.close();
            }
        }
    }

    private static class DropSchema extends Command {
        private DropSchema(final Command parent) {
            super("drop-schema", parent);

            setSummary("Remove all database objects");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            final TubaConnection conn = Tuba.getConnection();

            try {
                conn.open();
                conn.setWriteEnabled(true);

                RuntimeModule.getModule().getSchema().drop(conn);

                conn.commit();
            } finally {
                conn.close();
            }
        }
    }
}
