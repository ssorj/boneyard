package tuba.util.mpeg;

import java.io.*;

class TransportStreamPacket {
    byte[] bytes = new byte[188];
    private byte m_sync;
    private boolean m_error;
    private boolean m_start;
    private boolean m_priority;
    private int m_pid;
    private int m_scramble;
    private int m_aoff, m_alen;
    private int m_poff, m_plen;

    void parse() {
        m_sync = bytes[0];
        m_error = (0x80 & bytes[1]) != 0;
        m_start = (0x40 & bytes[1]) != 0;
        m_priority = (0x20 & bytes[1]) != 0;
        m_pid = (0x1f & bytes[1]) << 8 | (0xff & bytes[2]);
        m_scramble = (0xc0 & bytes[3]) >>> 6;

        final int adaptation = (0x30 & bytes[3]) >>> 4;
        m_aoff = -1;
        m_alen = 0;
        m_poff = -1;
        m_plen = 0;

        switch (adaptation) {
        case 1:
            m_poff = 4;
            m_plen = 184;
            break;
        case 2:
            m_aoff = 4;
            m_alen = 184;
            break;
        case 3:
            m_aoff = 4;
            m_alen = (0xff & bytes[4]) + 1;
            m_poff = m_aoff + m_alen;
            m_plen = 188 - m_poff;
            break;
        }
    }

    byte getSyncByte() {
        return m_sync;
    }

    boolean isError() {
        return m_error;
    }

    boolean isUnitStart() {
        return m_start;
    }

    int getPid() {
        return m_pid;
    }

    int getAdaptationOffset() {
        return m_aoff;
    }

    int getAdaptationLength() {
        return m_alen;
    }

    int getPayloadOffset() {
        return m_poff;
    }

    int getPayloadLength() {
        return m_plen;
    }

    boolean hasPayload() {
        return m_poff != -1;
    }

    void copyPayload(final ElementaryStreamPacket packet) {
        final int poff = getPayloadOffset();
        final int plen = getPayloadLength();

        if (poff == -1) throw new IllegalStateException();

        //System.out.println(poff + " " + plen + " " + packet.length + " " + packet.bytes.length);

        System.arraycopy(bytes, poff, packet.bytes, packet.length, plen);

        packet.length += plen;
    }

    void print() {
        final PrintWriter out = new PrintWriter(System.out);

        printSummary(out);
        printBytes(out);
    }

    void printSummary(final PrintWriter out) {
        out.print("0x");
        out.print(Integer.toHexString(m_sync));

        out.print(" [");

        if (isError()) out.print("e");
        if (isUnitStart()) out.print("s");

        out.print("] 0x");

        out.print(Integer.toHexString(getPid()));

        out.print(" (");
        out.print(getAdaptationOffset());
        out.print(",");
        out.print(getAdaptationOffset() + getAdaptationLength());
        out.print(")");

        out.print(" (");
        out.print(getPayloadOffset());
        out.print(",");
        out.print(getPayloadOffset() + getPayloadLength());
        out.print(")");

        out.println();
        out.flush();
    }

    void printBytes(final PrintWriter out) {
        final String hex = hex(bytes);

        out.print("  ");

        for (int j = 0; j < 72; j += 8) {
            out.print(" . . . :");
        }

        out.println();

        out.println("  " + hex.substring(0, 72) + " 36");
        out.println("  " + hex.substring(72, 144) + " 72");
        out.println("  " + hex.substring(144, 216) + " 108");
        out.println("  " + hex.substring(216, 288) + " 144");
        out.println("  " + hex.substring(288, 360) + " 180");
        out.println("  " + hex.substring(360) + " 188");

        out.flush();
    }

    private static final char[] s_digits = {
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        'a', 'b', 'c', 'd', 'e', 'f'
    };

    private static String hex(final byte[] bytes) {
        char[] chars = new char[bytes.length * 2];

        for (int i = 0; i < bytes.length; i++) {
            byte b = bytes[i];
            chars[i * 2] = s_digits[(b & 0xf0) >> 4];
            chars[i * 2 + 1] = s_digits[b & 0x0f];
        }

        return new String(chars);
    }
}
