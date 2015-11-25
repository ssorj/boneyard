package wooly.widgets;

import java.util.*;
import wooly.*;

public abstract class FormWidget extends WoolyWidget {
    private final WoolyForm m_form;

    protected FormWidget(final String name,
                         final WoolyForm form) {
        super(name);

        if (form == null) throw new IllegalArgumentException();

        m_form = form;
    }

    public final WoolyForm getForm() {
        return m_form;
    }
}
