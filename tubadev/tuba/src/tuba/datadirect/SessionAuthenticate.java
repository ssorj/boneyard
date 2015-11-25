package tuba.datadirect;

import com.withay.http.*;
import java.io.*;
import java.net.*;
import java.security.*;

final class SessionAuthenticate {
    void run(final DataDirectSession session) throws DataDirectException {
        final URL url;

        try {
            url = new URL(session.getListingsUrl());
        } catch (MalformedURLException e) {
            throw new DataDirectException("Cannot parse URL", e);
        }

        final HttpURLConnection conn;

        try {
            conn = (HttpURLConnection) url.openConnection();
        } catch (IOException e) {
            throw new DataDirectException
                ("Failure opening connection to web service", e);
        }

        try {
            conn.setRequestMethod("POST");
        } catch (ProtocolException e) {
            throw new IllegalStateException(e);
        }

        session.log(1, "Connecting to listings service");

        try {
            conn.connect();
        } catch (IOException e) {
            throw new DataDirectException("Failure connecting", e);
        }

        conn.disconnect();

        session.log(1, "Creating digest client");

        final DigestClient client;

        try {
            client = new DigestClient(conn.getHeaderField("WWW-Authenticate"));
        } catch (BadAuthorizationException e) {
            throw new DataDirectException
                ("Failure during authentication", e);
        } catch (UnsupportedAlgorithmException e) {
            throw new DataDirectException
                ("Failure during authentication", e);
        } catch (UnsupportedQOPException e) {
            throw new DataDirectException
                ("Failure during authentication", e);
        } catch (NoSuchAlgorithmException e) {
            throw new DataDirectException
                ("Failure during authentication", e);
        }

        client.setUsername(session.getUser());
        client.setPassword(session.getPassword());

        session.log(1, "Generating authorization");

        final String auth;

        try {
            auth = client.getAuthorization("POST", url.getFile());
        } catch (BadAuthorizationException e) {
            throw new DataDirectException
                ("Failure during authentication", e);
        }

        session.setAuthorization(auth);
    }
}
