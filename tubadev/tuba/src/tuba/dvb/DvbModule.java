package tuba.dvb;

import java.io.*;
import smoky.*;
import wheaty.*;
import tuba.runtime.*;

public final class DvbModule extends SmokyModule {
    public static DvbModule getModule() {
        return (DvbModule) Tuba.getModule("dvb");
    }

    private final DvbCommand m_command;
    private final ChannelFile m_channels;
    private final DvbTunerConfig m_tconfig;
    private DvbTuner m_tuner;

    public DvbModule(final SmokyRuntime runtime) {
        super("dvb", runtime);

        m_command = new DvbCommand(Tuba.getCommand());
        m_channels = new ChannelFile();

        m_tconfig = new DvbTunerConfig();
        getModel().addParameter(m_tconfig);
    }

    protected void initialize(final WheatySession session) {
        final File file = new File
            (Tuba.getRuntime().getConfigDirectory(), "dvb.channels");

        if (!file.exists()) {
            throw new TubaException
                ("Channel file '" + file.getPath() + "' not found");
        }

        try {
            getChannels().load(file);
        } catch (IOException e) {
            throw new IllegalStateException
                ("Failed reading channel file '" + file.getPath() + "'", e);
        }

        m_tuner = new DvbTuner(m_tconfig.getAdapter(session),
                               m_tconfig.getFrontend(session),
                               m_tconfig.getDemux(session),
                               m_tconfig.getDvr(session));
    }

    protected void startup() {
    }

    protected void shutdown() {
    }

    public DvbTuner getTuner() {
        return m_tuner;
    }

    DvbCommand getCommand() {
        return m_command;
    }

    ChannelFile getChannels() {
        return m_channels;
    }
}
