package wooly.lang;

import java.util.*;
import wooly.*;
import wooly.widgets.*;

class ModesNode extends Node {
    WoolyWidget build(final NodeTree tree) {
        return new ModalPane(name, tree.getModel());
    }
}
