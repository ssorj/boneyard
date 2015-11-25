package tuba.util;

public class CommandException extends Exception {
    private static final long serialVersionUID = 197511081L;

    public CommandException(final String message, final Throwable cause) {
        super(message, cause);
    }

    public CommandException(final String message) {
        super(message);
    }

    public CommandException(final Throwable cause) {
        super(cause);
    }
}
