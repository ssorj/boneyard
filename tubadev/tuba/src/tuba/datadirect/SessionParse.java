package tuba.datadirect;

import java.io.*;
import java.net.*;
import java.util.*;
import org.jdom.*;
import org.jdom.input.*;
import org.jdom.filter.*;
import tuba.datadirect.xtvd.*;

final class SessionParse {
    XtvdElement run(final DataDirectSession session,
                    final URL url) throws IOException, JDOMException {
        final Reader reader = new BufferedReader
            (new InputStreamReader(url.openStream(), "UTF-8"));

        final SAXBuilder builder = new SAXBuilder();

        builder.setFactory(new XtvdFactory());
        builder.setValidation(false);
        builder.setEntityResolver(null);

        final Document doc = builder.build(reader);

        final XtvdElement root;

        if (doc.getRootElement().getName().equals("xtvd")) {
            root = (XtvdElement) doc.getRootElement();
        } else {
            final Iterator elems = doc.getRootElement().getDescendants
                (new ElementFilter("xtvd"));

            if (elems.hasNext()) {
                root = (XtvdElement) elems.next();
            } else {
                throw new DataDirectException
                    ("Failed to find xtvd element in document");
            }
        }

        return root;
    }
}
