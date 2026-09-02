import java.sql.SQLException;
import java.sql.Statement;

public class SafeJdbcStatementExecute {
    static void updateUser(Statement statement, String userInput) throws SQLException {
        statement.execute(userInput);
    }
}
