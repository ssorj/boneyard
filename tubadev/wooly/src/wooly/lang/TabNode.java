package wooly.lang;

import java.util.*;
import wooly.*;
import wooly.widgets.*;

class TabNode extends Node {
    Node ntab;
    String smode;

    void configure(final NodeTree tree) {
        System.out.println("Yo1111!");

        final Tabs tabs = (Tabs) tree.getWidget(this.parent);
        final WoolyWidget tab = tree.getWidget(ntab);
        final WoolyWidget mode = tree.getWidget(smode);

        tabs.map(tab, mode);
    }
}
