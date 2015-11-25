package tuba.runtime;

public class TubaException extends RuntimeException {
    private static final long serialVersionUID = 197511082L;

    public TubaException(final String message) {
        super(message);
    }

    public TubaException(final String message, final Throwable cause) {
        super(message, cause);
    }
}
