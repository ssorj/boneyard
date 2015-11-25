package wooly.test;

import wooly.*;

public class TestHeader extends WoolyWidget {
    public TestHeader(final String name, final WoolyModel model) {
        super(name, model);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<h3>Wooly Widget Test</h3>");
        writer.write("<hr/>");
    }
}
