package tuba.runtime;

public final class DataException extends RuntimeException {
    public DataException(final Throwable cause) {
        super(cause);
    }

    public DataException(final String message, final Throwable cause) {
        super(message, cause);
    }
}
