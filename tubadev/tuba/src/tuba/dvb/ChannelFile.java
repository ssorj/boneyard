package tuba.dvb;

import java.io.*;
import java.util.*;

final class ChannelFile {
    private final Map m_channels;

    ChannelFile() {
        m_channels = new LinkedHashMap();
    }

    Channel get(final String callsign) {
        return (Channel) m_channels.get(callsign);
    }

    Iterator iterator() {
        return m_channels.values().iterator();
    }

    void load(final File file) throws IOException {
        final FileInputStream in = new FileInputStream(file);
        final InputStreamReader reader = new InputStreamReader(in, "UTF-8");

        load(new BufferedReader(reader));
    }

    void load(final BufferedReader reader) throws IOException {
        String line;

        while ((line = reader.readLine()) != null) {
            final String[] elems = line.split(":");
            final Channel chan = new Channel();

            m_channels.put(elems[0], chan);

	    chan.setCallSign(elems[0]);
            chan.setFrequency(Integer.parseInt(elems[1]));
            chan.setModulation(elems[2]);
            chan.setVideoPid(Integer.parseInt(elems[3]));
            chan.setAudioPid(Integer.parseInt(elems[4]));
	    chan.setSubchannel(Integer.parseInt(elems[5]));

            if (elems.length == 7) {
                chan.setFormat(elems[6]);
            }
        }
    }
}
