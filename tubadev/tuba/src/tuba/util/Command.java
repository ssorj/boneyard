package tuba.util;

import java.io.*;
import java.util.*;

public abstract class Command {
    private final String m_name;
    private final Command m_parent;
    private final Map m_children;
    private final Map m_aliases;
    private String m_psyntax;
    private String m_summary;
    private Command m_delegate;

    public Command(final String name, final Command parent) {
        m_name = name;
        m_parent = parent;
        m_children = new LinkedHashMap();
        m_aliases = new HashMap();

        if (getParent() != null) {
            getParent().getChildren().put(getName(), this);
        }
    }

    public final String getName() {
        return m_name;
    }

    public final Command getParent() {
        return m_parent;
    }

    final Map getChildren() {
        return m_children;
    }

    public final Command getChild(final String name) {
        Command child = (Command) getChildren().get(name);

        if (child == null) {
            child = (Command) getAliases().get(name);
        }

        return child;
    }

    public final void addAlias(final String alias) {
        if (getParent() == null) throw new IllegalStateException();

        getParent().getAliases().put(alias, this);
    }

    private final Map getAliases() {
        return m_aliases;
    }

    public final String getParameterSyntax() {
        return m_psyntax;
    }

    public final void setParameterSyntax(final String syntax) {
        m_psyntax = syntax;
    }

    public final String getSummary() {
        return m_summary;
    }

    public final void setSummary(final String summary) {
        m_summary = summary;
    }

    public final Command getDelegate() {
        return m_delegate;
    }

    public final void setDelegate(final Command delegate) {
        m_delegate = delegate;
    }

    private Command resolve(final LinkedList args) throws CommandException {
        if (getChildren().size() == 0 || args.size() == 0) {
            return this;
        } else {
            final String arg = (String) args.removeFirst();
            final Command command = getChild(arg);

            if (command == null) {
                throw new CommandException("command exception");
            } else {
                return command.resolve(args);
            }
        }
    }

    public void run(final CommandArguments args,
                    final BufferedReader in,
                    final PrintWriter out,
                    final PrintWriter err)
            throws CommandException, IOException {
        if (getDelegate() != null) {
            getDelegate().run(args, in, out, err);
        }
    }

    public final int execute(final List args,
                             final BufferedReader in,
                             final PrintWriter out,
                             final PrintWriter err) throws IOException {
        int ret = 1;

        try {
            final LinkedList largs = new LinkedList(args);
            final Command command = resolve(largs);
            final CommandArguments cargs = new CommandArguments
                (command, largs);

            command.run(cargs, in, out, err);

            ret = 0;
        } catch (CommandException e) {
            err.println(e.getMessage());
        }

        return ret;
    }
}
