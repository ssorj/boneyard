package tuba.datadirect;

import java.io.*;
import java.net.*;
import org.jdom.*;
import tuba.runtime.*;
import tuba.runtime.model.*;
import tuba.datadirect.xtvd.*;
import tuba.util.*;

public final class DataDirectSession extends Session {
    private String m_user;
    private String m_password;
    private String m_url;
    private String m_auth;

    DataDirectSession() {
        super("datadirect");
    }

    String getUser() {
        return m_user;
    }

    void setUser(final String user) {
        m_user = user;
    }

    String getPassword() {
        return m_password;
    }

    void setPassword(final String password) {
        m_password = password;
    }

    String getListingsUrl() {
        return m_url;
    }

    void setListingsUrl(final String url) {
        m_url = url;
    }

    public String getAuthorization() {
        return m_auth;
    }

    // XXX public?
    public void setAuthorization(final String auth) {
        m_auth = auth;
    }

    public void authenticate() {
        final SessionAuthenticate auth = new SessionAuthenticate();

        auth.run(this);
    }

    public URL fetch() throws DataDirectException {
        final SessionFetch fetch = new SessionFetch();

        final URL url = fetch.run(this);

        return url;
    }

    public XtvdElement parse(final URL url) throws DataDirectException {
        final SessionParse parse = new SessionParse();
        final XtvdElement root;

        try {
            root = parse.run(this, url);
        } catch (IOException e) {
            throw new DataDirectException("Parse failure", e);
        } catch (JDOMException e) {
            throw new DataDirectException("Parse failure", e);
        }

        return root;
    }

    public void save(final XtvdElement root) {
        final SessionSave save = new SessionSave();
        final TubaConnection conn = Tuba.getConnection();

        try {
            conn.open();
            conn.setWriteEnabled(true);

            save.run(conn, root);

            conn.commit();
        } finally {
            conn.close();
        }
    }

    public void update() throws DataDirectException {
        save(parse(fetch()));
    }
}
