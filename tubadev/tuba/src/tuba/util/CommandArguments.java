package tuba.util;

import java.io.*;
import java.util.*;
import java.math.*;

public final class CommandArguments {
    private final Command m_command;
    private final Map m_options;
    private final List m_params;
    private final List m_errors;

    CommandArguments(final Command command, final LinkedList args) {
        m_command = command;
        m_options = new HashMap();
        m_params = new ArrayList();
        m_errors = new ArrayList();

        parse(args, null);
    }

    private void parse(final LinkedList args,
                       final String option) {
        if (args.size() != 0) {
            final String arg = (String) args.removeFirst();

            if (arg.startsWith("-")) {
                final String opt = arg.substring(1);

                getOptions().put(opt, null);

                parse(args, opt);
            } else {
                if (option != null) {
                    getOptions().put(option, arg);
                } else {
                    getParameters().add(arg);
                }

                parse(args, null);
            }
        }
    }

    private Map getOptions() {
        return m_options;
    }

    private List getParameters() {
        return m_params;
    }

    private List getErrors() {
        return m_errors;
    }

    public String require(final int param) throws CommandException {
        final String string = get(param);

        if (string == null) {
            final SyntaxError error = new SyntaxError();
            error.Parameter = param;
            error.Message = "Value is required";
            getErrors().add(error);
        }

        return string;
    }

    public String get(final int param) {
        String string = null;

        try {
            string = (String) getParameters().get(param);
        } catch (IndexOutOfBoundsException e) {
        }

        return string;
    }

    public BigInteger getBigInteger(final int param) throws CommandException {
        final String string = get(param);
        BigInteger number = null;

        if (string != null) {
            try {
                number = new BigInteger(string);
            } catch (NumberFormatException e) {
                final SyntaxError error = new SyntaxError();
                error.Parameter = param;
                error.Message = "Value is not a valid integer";
                getErrors().add(error);
            }
        }

        return number;
    }

    public Long getLong(final int param) throws CommandException {
        final BigInteger integer = getBigInteger(param);
        Long number = null;

        if (integer != null) {
            number = new Long(integer.longValue());
        }

        return number;
    }

    public Integer getInteger(final int param) throws CommandException {
        final BigInteger integer = getBigInteger(param);
        Integer number = null;

        if (integer != null) {
            number = new Integer(integer.intValue());
        }

        return number;
    }

    public Integer getInteger(final int param,
                              final Integer defaalt) throws CommandException {
        Integer integer = getInteger(param);

        if (integer == null) {
            integer = defaalt;
        }

        return integer;
    }

    public void check(final PrintWriter out) throws CommandException {
        if (getErrors().size() != 0) {
            final Iterator iter = getErrors().iterator();

            while (iter.hasNext()) {
                final SyntaxError error = (SyntaxError) iter.next();

                error.print(out);
            }

            throw new CommandException("Syntax error");
        }
    }

    private static class SyntaxError {
        public int Parameter;
        public String Message;

        void print(final PrintWriter out) {
            out.println("Parameter " + (Parameter + 1) + ": " + Message);
        }
    }
}
