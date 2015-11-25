package tuba.runtime;

import java.io.*;
import java.util.*;
import tuba.util.*;
import smoky.*;
import wheaty.*;

public final class ConfigCommand extends Command {
    ConfigCommand() {
        super("tuba-config", null);

        setDelegate(new HelpCommand(this));

        new Get(this);
        new Set(this);
        new Print(this);
    }

    private static String toString(final Object object) {
	final String string;

	if (object == null) {
	    string = "[null]";
	} else if (object instanceof String) {
	    string = "\"" + object + "\"";
	} else {
	    string = object.toString();
	}

	return string;
    }

    private static class Print extends Command {
	private Print(final Command parent) {
	    super("print", parent);

	    setSummary("Print the current configuration");
	}

	public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err) throws IOException {
            final TubaRuntime runtime = Tuba.getRuntime();

            final SmokyConfig config = Tuba.getConfig();
            config.load();

            for (final SmokyModule module : runtime.getModules()) {
                final WheatyModel model = module.getModel();

                for (final WheatyParameter param : model.getParameters()) {
                    out.print(model.getName());
                    out.print(":");
                    out.print(param.getPath());
                    out.print(" = ");

                    final Object value = param.get
                        (Tuba.getConfig());

                    out.print(ConfigCommand.toString(value));

                    if (value == null) {
                        if (param.get() == null) {
                            out.print(" [default]");
                        }
                    } else if (value.equals(param.get())) {
                        out.print(" [default]");
                    }

                    out.println();
                }
            }
	}
    }

    private static WheatyParameter lookup(final String key)
            throws CommandException {
        final String[] elems = key.split("\\:");
        final String smodule;
        final String sparam;

        switch (elems.length) {
        case 2:
            smodule = elems[0];
            sparam = elems[1];
            break;
        default:
            throw new CommandException
                ("Parameter name '" + key + "' malformed");
        }

        final SmokyModule module = Tuba.getRuntime().getModule(smodule);

        if (module == null) {
            throw new CommandException
                ("Module '" + smodule + "' not found");
        }

        final WheatyParameter param = module.getModel().getParameter
            (sparam);

        if (param == null) {
            throw new CommandException
                ("Parameter '" + sparam + "' not found");
        }

        return param;
    }

    private static class Get extends Command {
	private Get(final Command parent) {
	    super("get", parent);

	    setParameterSyntax("MODEL:PARAM");
	    setSummary("Gets the value of parameter MODEL:PARAM");
	}

	public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            final String key = args.require(0);

            args.check(err);

	    final SmokyConfig config = Tuba.getConfig();
            config.load();

            final WheatyParameter param = lookup(key);
	    final Object value = param.get(config);

	    out.println(value);
	}
    }

    private static class Set extends Command {
        private Set(final Command parent) {
            super("set", parent);

	    setParameterSyntax("MODEL:PARAM VALUE");
	    setSummary("Sets parameter MODEL:PARAM to VALUE");
        }

        public void run(final CommandArguments args,
                        final BufferedReader in,
                        final PrintWriter out,
                        final PrintWriter err)
                throws CommandException, IOException {
            final String key = args.require(0);
            final String svalue = args.require(1);

            args.check(err);

	    final SmokyConfig config = Tuba.getConfig();
            config.load();

	    final WheatyParameter param = lookup(key);

            final WheatyValue value = new WheatyValue("tmp");
	    value.set(svalue);

	    final Object object = param.unmarshal(value);
	    param.set(config, object);

	    config.save();
        }
    }

    public static final void main(final String[] sargs) {
        int exit = 1;

        try {
            final Command root = new ConfigCommand();
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
        }

        System.exit(exit);
    }
}
