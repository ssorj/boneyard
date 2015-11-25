package wooly.server;

import java.io.*;
import java.net.*;

final class UrlCodec {
    public static String encode(final String decoded) {
        try {
            return URLEncoder.encode(decoded, "UTF-8");
        } catch (UnsupportedEncodingException e) {
            throw new IllegalStateException(e.getMessage());
        }
    }

    public static String decode(final String encoded) {
        try {
            return URLDecoder.decode(encoded, "UTF-8");
        } catch (UnsupportedEncodingException e) {
            throw new IllegalStateException(e.getMessage());
        }
    }
}
