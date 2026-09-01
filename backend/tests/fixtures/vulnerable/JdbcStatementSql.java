import java.sql.SQLException;
import java.sql.Statement;

public class JdbcStatementSql {
    static void findUser(Statement statement, String userInput) throws SQLException {
        statement.executeQuery(userInput);
    }
}
