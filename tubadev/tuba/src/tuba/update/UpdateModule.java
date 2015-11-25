package tuba.update;

import butyl.*;
import smoky.*;
import wheaty.*;
import wheaty.parameters.*;
import tuba.runtime.*;

public final class UpdateModule extends SmokyModule {
    private final StringParameter m_adapterp;
    private final UpdateThread m_thread;
    private UpdateTimer m_timer;
    private UpdateAdapter m_adapter;

    public static final UpdateModule get() {
        return (UpdateModule) Tuba.getModule("update");
    }

    public UpdateModule(final SmokyRuntime runtime) {
        super("update", runtime);

        m_adapterp = new StringParameter("adapter");
        m_adapterp.setNullable(false);
        m_adapterp.set("tuba.datadirect.DataDirectAdapter");

        getModel().addParameter(m_adapterp);

        m_thread = new UpdateThread(this);
    }

    protected void initialize(final WheatySession session) {
        m_adapter = (UpdateAdapter)
            ReflectFunctions.newInstance((String) m_adapterp.get(session));
    }

    protected void startup() {
        if (m_timer != null) throw new IllegalStateException();

        getThread().start();

        m_timer = new UpdateTimer(this);
    }

    protected void shutdown() {
        if (m_timer == null) throw new IllegalStateException();

        m_timer.cancel();
        m_timer = null;

        getThread().stop();
    }

    UpdateAdapter getAdapter() {
        return m_adapter;
    }

    UpdateThread getThread() {
        return m_thread;
    }

    UpdateTimer getTimer() {
        return m_timer;
    }
}
