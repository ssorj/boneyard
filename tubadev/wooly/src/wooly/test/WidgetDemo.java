package wooly.test;

import java.io.*;
import java.net.*;
import java.util.*;
import wooly.*;
import wooly.lang.*;
import wooly.server.*;
import wooly.widgets.*;

public final class WidgetDemo extends WoolyApplication {
    public WidgetDemo(final String name, final WoolyApplication parent) {
        super(name, parent);

        final WoolyPage page = (WoolyPage) WidgetParser.parse
            (WidgetDemo.class.getResource("WidgetDemo.wool"));

        setWidget(page);
    }

    public static void main(final String[] args) throws Exception {
        final WoolyServer server = WoolyServer.create(8080);

        final WidgetDemo demo = new WidgetDemo("demo", null);
        server.setApplication(demo);

        server.run();
    }
}
