import java.sql.SQLException;
import java.sql.Statement;

public class JdbcStatementUpdateSql {
    private static void updateUser(Statement statement, String userInput) throws SQLException {
        statement.executeUpdate(userInput);
    }
}
