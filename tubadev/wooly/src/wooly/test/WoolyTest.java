package wooly.test;

import java.io.*;
import java.net.*;
import java.util.*;
import wooly.*;
import wooly.debug.*;
import wooly.lang.*;
import wooly.server.*;
import wooly.widgets.*;

public final class WoolyTest {
    public static void main(final String[] args) throws Exception {
        final WoolyServer server = WoolyServer.create(8080);

        final WoolyApplication root = new WoolyApplication("root", null);
        server.setApplication(root);
        root.setWidget(new RootPage("root", root));
        root.getTitle().set("Test Applications");

        final WoolyApplication toggle = new WoolyApplication
            ("ToggleLink", root);
        toggle.setWidget(new TogglePage("root", toggle));
        toggle.getTitle().set("Toggle Links");

        final WoolyApplication tabs = new WoolyApplication
            ("TabbedPane", root);
        tabs.setWidget(new TabsPage("root", tabs));
        tabs.getTitle().set("Tabbed Pane");

        final WoolyApplication form = new WoolyApplication
            ("WoolyForm", root);
        form.setWidget(new FormPage("root", form));
        form.getTitle().set("Forms");

        final WoolyApplication reflect = new WoolyApplication
            ("reflect", root);
        final URL url = WoolyTest.class.getResource("TestPage.wool");
        final WoolyPage page = (WoolyPage) WidgetParser.parse(url);
        page.setApplication(reflect);
        reflect.setWidget(page);
        reflect.getTitle().set("Reflect");

        new DebugApplication("debug", root);

        server.run();
    }

    private static class RootPage extends TestPage {
        RootPage(final String name, final WoolyApplication app) {
            super(name, app);

            add(new ApplicationDirectory("appdir"));
        }
    }

    private static class TogglePage extends TestPage {
        private static final int s_dim = 3;

        private final ToggleLink[][] m_links;

        TogglePage(final String name, final WoolyApplication app) {
            super(name, app);

            m_links = new ToggleLink[s_dim][s_dim];

            final WoolyContainer body = new WoolyContainer("body");
            add(body);

            for (int i = 0; i < s_dim; i++) {
                final ToggleLink[] row = m_links[i];

                for (int j = 0; j < s_dim; j++) {
                    final int index = (i * s_dim) + j;

                    final ToggleLink link = new ToggleLink("toggle" + index);
                    body.add(link);

                    final Label label = new Label("label");
                    label.getText().set("Toggle " + index);
                    link.add(label);

                    row[j] = link;
                }
            }
        }

        protected void renderBody(final WoolySession session,
                                  final WoolyWriter writer) {
            writer.write("<table>");

            for (final ToggleLink[] row : m_links) {
                writer.write("<tr>");

                for (final ToggleLink link : row) {
                    writer.write("<td>");
                    writer.write(link.render(session));
                    writer.write("</td>");
                }

                writer.write("</tr>");
            }

            writer.write("</table>");
        }
    }

    private static class TabsPage extends TestPage {
        TabsPage(final String name, final WoolyApplication app) {
            super(name, app);

            final TabbedPane tabs = new TabbedPane("tabs");
            add(tabs);

            for (int i = 0; i < 10; i++) {
                final Label label = new Label("body" + i);
                label.getText().set("Body " + i);

                tabs.addTab(label, "Tab " + i);
            }
        }
    }

    private static class FormPage extends TestPage {
        FormPage(final String name, final WoolyApplication app) {
            super(name, app);

            final WoolyContainer body = new WoolyContainer("body");
            add(body);

            final ToggleLink link = new ToggleLink("toggle");
            body.add(link);

            final Label label = new Label("text");
            label.setText("Testing!");
            link.add(label);

            final WoolyForm form = new WoolyForm("form");
            body.add(form);

            final TextField email = new TextField("email", form);
            email.getLabel().setText("Email Address");
            form.add(email);

            final TextField first = new TextField("first", form);
            first.getLabel().setText("First Name");
            form.add(first);

            final TextField last = new TextField("last", form);
            last.getLabel().setText("Last Name");
            form.add(last);

            final ButtonField submit = new ButtonField("submit", form);
            submit.getLabel().setText("Submit");
            form.add(submit);
        }
    }

    private static class TestPage extends WoolyPage {
        TestPage(final String name, final WoolyApplication app) {
            super(name, app);

            add(new ApplicationContextPath("appctx"));
        }
    }
}
