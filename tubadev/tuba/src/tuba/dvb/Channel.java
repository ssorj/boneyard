package tuba.dvb;

import java.io.*;

final class Channel {
    private String m_callsign;
    private int m_freq;
    private String m_modulation;
    private int m_vpid;
    private int m_apid;
    private int m_subchan;
    private String m_format;

    String getCallSign() {
	return m_callsign;
    }

    void setCallSign(final String callsign) {
	m_callsign = callsign;
    }

    int getFrequency() {
	return m_freq;
    }

    void setFrequency(final int freq) {
	m_freq = freq;
    }

    String getModulation() {
	return m_modulation;
    }

    void setModulation(final String modulation) {
	m_modulation = modulation;
    }

    int getVideoPid() {
	return m_vpid;
    }

    void setVideoPid(final int vpid) {
	m_vpid = vpid;
    }

    int getAudioPid() {
	return m_apid;
    }

    void setAudioPid(final int apid) {
	m_apid = apid;
    }

    int getSubchannel() {
	return m_subchan;
    }

    void setSubchannel(final int subchan) {
	m_subchan = subchan;
    }

    String getFormat() {
        return m_format;
    }

    void setFormat(final String format) {
        m_format = format;
    }

    void print(final PrintWriter writer) {
        writer.print(getCallSign());
        writer.println();
    }
}
