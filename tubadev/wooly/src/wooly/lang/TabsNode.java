package wooly.lang;

import java.util.*;
import wooly.*;
import wooly.widgets.*;

class TabsNode extends Node {
    String smodes;

    WoolyWidget build(final NodeTree tree) {
        return new Tabs(name, tree.getModel());
    }

    void configure(final NodeTree tree) {
        final Tabs tabs = (Tabs) tree.getWidget(this);
        final ModalPane modes = (ModalPane) tree.getWidget(smodes);

        tabs.setModes(modes);
    }
}
