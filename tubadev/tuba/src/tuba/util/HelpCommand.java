package tuba.util;

import java.io.*;
import java.util.*;

public class HelpCommand extends Command {
    public HelpCommand(final Command parent) {
        super("help", parent);

        setSummary("Print this information");
    }

    public void run(final CommandArguments args,
                    final BufferedReader in,
                    final PrintWriter out,
                    final PrintWriter err) {
        out.println("Commands of '" + getParent().getName() + "':");

        final Iterator commands = getParent().getChildren
            ().values().iterator();

        while (commands.hasNext()) {
            final Command command = (Command) commands.next();

            if (command.getName().startsWith(":")) {
                continue;
            }

            out.print("  " + command.getName());

            if (command.getParameterSyntax() != null) {
                out.print(" " + command.getParameterSyntax());
            }

            out.println();

            if (command.getSummary() != null) {
                out.println("    " + command.getSummary());
            }
        }
    }
}
