package tuba.dvb;

import tuba.runtime.*;
import wheaty.*;
import wheaty.parameters.*;

final class DvbTunerConfig extends StructParameter {
    private final StringParameter m_adapter;
    private final StringParameter m_frontend;
    private final StringParameter m_demux;
    private final StringParameter m_dvr;

    DvbTunerConfig() {
        super("tuner");

        m_adapter = new StringParameter("adapter");
        m_adapter.setNullable(false);
        m_adapter.set("/dev/dvb/adapter0");

        m_frontend = new StringParameter("frontend");
        m_frontend.setNullable(false);
        m_frontend.set("frontend0");

        m_demux = new StringParameter("demux");
        m_demux.setNullable(false);
        m_demux.set("demux0");

        m_dvr = new StringParameter("dvr");
        m_dvr.setNullable(false);
        m_dvr.set("dvr0");

        addChild(m_adapter);
        addChild(m_frontend);
        addChild(m_demux);
        addChild(m_dvr);
    }

    String getAdapter(final WheatySession session) {
        return (String) m_adapter.get(session);
    }

    String getFrontend(final WheatySession session) {
        return (String) m_frontend.get(session);
    }

    String getDemux(final WheatySession session) {
        return (String) m_demux.get(session);
    }

    String getDvr(final WheatySession session) {
        return (String) m_dvr.get(session);
    }
}
