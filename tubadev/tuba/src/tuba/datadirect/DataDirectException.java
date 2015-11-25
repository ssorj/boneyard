package tuba.datadirect;

public final class DataDirectException extends IllegalStateException {
    private static final long serialVersionUID = 197511083L;

    DataDirectException(final String message, final Throwable t) {
        super(message, t);
    }

    DataDirectException(final String message) {
        super(message);
    }
}
