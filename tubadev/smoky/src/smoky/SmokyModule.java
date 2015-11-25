package smoky;

import wheaty.*;

public abstract class SmokyModule {
    private final String m_name;
    private final SmokyRuntime m_runtime;
    private final WheatyModel m_model;

    public SmokyModule(final String name, final SmokyRuntime runtime) {
        m_name = name;
        m_runtime = runtime;
        m_model = new WheatyModel(getName());

        getRuntime().addModule(this);
    }

    public final String getName() {
        return m_name;
    }

    public final SmokyRuntime getRuntime() {
        return m_runtime;
    }

    public final WheatyModel getModel() {
        return m_model;
    }

    protected abstract void initialize(final WheatySession session);

    protected abstract void startup();

    protected abstract void shutdown();

    public final void log(final Exception e) {
        getRuntime().log(e);
    }

    public final void log(final String message) {
        getRuntime().log(message);
    }

    public final void log(final int threshold, final String message) {
        getRuntime().log(threshold, message);
    }
}
