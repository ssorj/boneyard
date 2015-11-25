package wooly.test;

import wooly.*;

public class TestFooter extends WoolyWidget {
    public TestFooter(final String name, final WoolyModel model) {
        super(name, model);
    }

    protected void doRender(final WoolySession session,
                            final WoolyWriter writer) {
        writer.write("<hr/>");
        writer.write("<address>justin@ross.name</address>");
    }
}
