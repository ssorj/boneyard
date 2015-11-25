package tuba.datadirect;

import java.io.*;
import java.net.*;
import java.util.*;
import java.util.zip.*;
import tuba.util.*;

final class SessionFetch {
    private Template s_request = new Template
        (SessionFetch.class, "fetch-request.xml");

    URL run(final DataDirectSession session) throws DataDirectException {
        final long now = System.currentTimeMillis();

        return run(session, new Date(now), new Date(now + 5 * 86400000));
    }

    URL run(final DataDirectSession session,
            final Date start,
            final Date end) throws DataDirectException {
        session.log(1, "Opening connection");

        final URL listings;

        try {
            listings = new URL(session.getListingsUrl());
        } catch (MalformedURLException e) {
            throw new DataDirectException("Cannot parse URL", e);
        }

        final HttpURLConnection conn;

        try {
            conn = (HttpURLConnection) listings.openConnection();
        } catch (IOException e) {
            throw new DataDirectException
                ("Failure opening connection to web service", e);
        }

        try {
            conn.setRequestMethod("POST");
        } catch (ProtocolException e) {
            throw new IllegalStateException(e);
        }

        conn.setDoInput(true);
        conn.setDoOutput(true);
        conn.setUseCaches(false);

        session.log(1, "Preparing request");

        conn.setRequestProperty("Authorization", session.getAuthorization());
        conn.setRequestProperty("Accept-Encoding", "gzip");
        conn.setRequestProperty
            ("SOAPAction", "urn:TMSWebServices:xtvdWebService#download");

        final Map vars = new HashMap();
        vars.put("startTime", Formats.formatTime(start));
        vars.put("endTime", Formats.formatTime(end));

        final String request = s_request.interpolate(vars);

        session.log(1, "Writing request");

        try {
            writeRequest(conn, request);
        } catch (IOException e) {
            throw new DataDirectException("Failure writing request", e);
        }

        final File file;

        try {
            final long secs = System.currentTimeMillis() / 1000;
            file = File.createTempFile("datadirect-response-" + secs, null);
        } catch (IOException e) {
            throw new DataDirectException
                ("Failure creating temporary file", e);
        }

        session.log(1, "Reading response");

        try {
            readResponse(conn, file);
        } catch (IOException e) {
            throw new DataDirectException("Failure reading response", e);
        }

        final URL url;

        try {
            url = file.toURL();
        } catch (MalformedURLException e) {
            throw new IllegalStateException(e);
        }

        return url;
    }

    private void writeRequest(final HttpURLConnection conn,
                              final String request) throws IOException {
        final Writer writer = new BufferedWriter
            (new OutputStreamWriter(conn.getOutputStream(), "UTF-8"));

        writer.write(request);

        writer.close();
    }

    private void readResponse(final HttpURLConnection conn,
                              final File file) throws IOException {
        final BufferedReader reader = getReader(conn);
        final BufferedWriter writer = new BufferedWriter(new FileWriter(file));
        String line;

        while ((line = reader.readLine()) != null) {
            writer.write(line);
            writer.newLine();
        }

        reader.close();
        writer.close();
    }

    private BufferedReader getReader(final HttpURLConnection conn)
            throws IOException {
        InputStream in = conn.getInputStream();
	String header = conn.getHeaderField("Content-Encoding");

	if (header == null) {
	    header = conn.getHeaderField("Content-encoding");
	}

	if (header != null && header.equals("gzip")) {
            in = new GZIPInputStream(conn.getInputStream());
        }

        final BufferedReader reader = new BufferedReader
            (new InputStreamReader(in, "UTF-8"));

        return reader;
    }
}
