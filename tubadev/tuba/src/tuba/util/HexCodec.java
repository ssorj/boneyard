package tuba.util;

public final class HexCodec {
    private static final char[] s_digits = {
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9',
        'a', 'b', 'c', 'd', 'e', 'f'
    };

    public static String encode(final byte[] bytes) {
        char[] chars = new char[bytes.length * 2];

        for (int i = 0; i < bytes.length; i++) {
            byte b = bytes[i];
            chars[i * 2] = s_digits[(b & 0xf0) >> 4];
            chars[i * 2 + 1] = s_digits[b & 0x0f];
        }

        return new String(chars);
    }
}
