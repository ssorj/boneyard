package wooly.lang;

import java.util.*;
import wooly.*;

class PageNode extends Node {
    String title;

    WoolyWidget build(final NodeTree tree) {
        final WoolyPage page = new WoolyPage(name, tree.getModel());
        page.getTitle().set(title);

        return page;
    }
}
