package tuba.web;

import java.io.*;
import java.net.*;
import java.util.*;
import lentil.*;
import tuba.runtime.*;
import tuba.runtime.model.*;
import tuba.util.*;
import wooly.*;
import wooly.server.*;
import wooly.widgets.*;

final class SeriesIndexPage extends WoolyPage {
    SeriesIndexPage(final WoolyModel model) {
        super("series-index", model);
    }
}