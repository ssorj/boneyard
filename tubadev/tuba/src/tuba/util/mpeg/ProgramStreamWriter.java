package tuba.util.mpeg;

import java.io.*;

final class ProgramStreamWriter {
    private byte[] m_pack = {
        // "pack_start_code" (32, 0x000001ba)
        (byte) 0x0, (byte) 0x0, (byte) 0x1, (byte) 0xba,
        // '01', "system_clock_reference_base" (3, 0), marker (1, 1),
        // "system_clock_reference_base" (15, 0), marker (1, 1),
        // "system_clock_reference_base", (15, 0), 
        (byte) 0x44, 0, 4, 0,
        4, 1,
        0, (byte) 0xea, 0x63, (byte) 0xf8
    };

    private byte[] m_end = {
        0, 0, 1, (byte) 0xb9
    };

    private byte[] m_system = {
        // "system_header_start_code" (32, 0x000001bb)
        (byte) 0x0, (byte) 0x0, (byte) 0x1, (byte) 0xbb,
        // "header_length" (16, 12)
        (byte) 0x0, (byte) 0xc,
        // marker (1, 1), "rate_bound" (22), marker (1, 1)
        (byte) 0x80, (byte) 0x9c, (byte) 0x41,
        // "audio_bound" (6, 1), "fixed_flag" (1, 0), "CSPS_flag" (1, 0)
        (byte) 0x4,
        // "system_audio_lock_flag" (1, 0), "system_video_lock_flag" (1, 0),
        // "video_bound" (5, 16), "packet_rate_restriction_flag" (1, 0)
        (byte) 0x20,
        // "reserved_byte" (8, 0xff)
        (byte) 0xff,
        // XXX hack
        (byte) 0xe0, (byte) 0xff, (byte) 0xff
    };

    private final OutputStream m_out;

    ProgramStreamWriter(final OutputStream out) {
        m_out = out;
    }

    void writePackHeader() throws IOException {
        m_out.write(m_pack);
    }

    void writeSystemHeader() throws IOException {
        m_out.write(m_system);
    }

    void writeEndCode() throws IOException {
        m_out.write(m_end);
    }

    void write(final ElementaryStreamPacket packet) throws IOException {
        m_out.write(packet.bytes);
    }
}
