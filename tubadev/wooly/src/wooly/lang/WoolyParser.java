package wooly.lang;

import java.io.*;
import java.net.*;
import java.util.*;
import wooly.*;

public final class WoolyParser {
    public static final WoolyWidget parse(final URL url,
                                          final WoolyModel model) {
        if (url == null) throw new IllegalArgumentException();

        final WidgetParser parser;

        try {
            parser = new WidgetParser(new InputStreamReader(url.openStream()));
        } catch (IOException e) {
            throw new IllegalStateException(e);
        }

        final Node node;

        try {
            node = parser.parse();
        } catch (ParseException e) {
            throw new IllegalStateException(e);
        }

        final NodeTree tree = new NodeTree(node, model);

        tree.index();

        System.out.println(tree.getNodes());

        final WoolyWidget widget = tree.build();

        System.out.println(tree.getWidgets());

        tree.configure();

        return widget;
    }
}