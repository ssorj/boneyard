package tuba.runtime;

import java.io.*;
import java.util.*;
import tuba.util.*;

public final class TubaCommand extends Command {
    TubaCommand() {
        super("tuba", null);

        setDelegate(new HelpCommand(this));

        ListCommands.add(this);
        RequestCommands.add(this);
        SchemaCommands.add(this);
    }

    public static final void main(final String[] sargs) {
        final TubaRuntime runtime = Tuba.getRuntime();

        runtime.initialize();

        int exit = 1;

        try {
            runtime.startup();

            final Command root = Tuba.getCommand();
            final LinkedList args = new LinkedList(Arrays.asList(sargs));
            final BufferedReader in = new BufferedReader
                (new InputStreamReader(System.in));
            final PrintWriter out = new PrintWriter(System.out, true);
            final PrintWriter err = new PrintWriter(System.err, true);

            exit = root.execute(args, in, out, err);
        } catch (Exception e) {
            try {
                e.printStackTrace();
            } catch (Exception ie) {
            }
        } finally {
            runtime.shutdown();
        }

        System.exit(exit);
    }
}
