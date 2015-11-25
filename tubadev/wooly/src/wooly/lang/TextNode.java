package wooly.lang;

import java.net.*;
import java.util.*;
import wooly.*;
import wooly.widgets.*;

class TextNode extends Node {
    String text;
    String url;

    WoolyWidget build(final NodeTree tree) {
        final Text wtext = new Text(name, tree.getModel());

        if (url == null) {
            wtext.setText(text);
        } else {
            try {
                wtext.setText(new URL(url));
            } catch (MalformedURLException e) {
                throw new IllegalStateException(e);
            }
        }

        return wtext;
    }
}
