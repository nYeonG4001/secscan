import java.sql.SQLException;
import java.sql.Statement;

public class SafeJdbcStatementAddBatch {
    static void updateUser(Statement statement, String userInput) throws SQLException {
        statement.addBatch(userInput);
    }
}
