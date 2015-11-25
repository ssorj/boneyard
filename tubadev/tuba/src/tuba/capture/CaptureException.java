package tuba.capture;

public final class CaptureException extends IllegalStateException {
    private static final long serialVersionUID = 197511084L;

    CaptureException(final String message, final Throwable t) {
        super(message, t);
    }

    CaptureException(final String message) {
        super(message);
    }

    CaptureException(final Throwable t) {
        super(t);
    }
}
