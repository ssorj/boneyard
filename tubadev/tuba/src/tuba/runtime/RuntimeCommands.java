package tuba.runtime;

import java.io.*;
import java.util.*;
import tuba.util.*;

final class RuntimeCommands {
    static void add(final Command parent) {
        new Startup(parent);
        new Shutdown(parent);
    }

    private static class Startup extends Command {
        Startup(final Command parent) {
            super("startup", parent);

            setSummary("Start up all server services");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err) {
            final TubaRuntime runtime = Tuba.getRuntime();

            synchronized (runtime) {
                if (runtime.isUp()) {
                    out.println("The runtime is already up");
                } else {
                    runtime.startup();
                }
            }
        }
    }

    private static class Shutdown extends Command {
        Shutdown(final Command parent) {
            super("shutdown", parent);

            setSummary("Shut down all server services");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err) {
            final TubaRuntime runtime = Tuba.getRuntime();

            synchronized (runtime) {
                if (runtime.isUp()) {
                    runtime.shutdown();
                } else {
                    out.println("The runtime is already down");
                }
            }
        }
    }
}
