package lentil;

import java.sql.*;

public final class LentilConnectionException extends IllegalStateException {
    LentilConnectionException(SQLException cause) {
        super(cause);
    }
}

