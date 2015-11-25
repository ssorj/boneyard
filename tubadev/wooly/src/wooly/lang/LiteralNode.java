package wooly.lang;

import java.util.*;
import wooly.*;
import wooly.widgets.*;

class LiteralNode extends Node {
    String text;

    WoolyWidget build(final NodeTree tree) {
        final Label label = new Label(name, tree.getModel());
        label.setText(text);

        return label;
    }
}
