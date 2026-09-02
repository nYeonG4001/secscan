import java.sql.SQLException;
import java.sql.Statement;

public class JdbcExecuteLargeUpdate {
    static void updateUser(Statement statement, String userInput) throws SQLException {
        statement.executeLargeUpdate(userInput);
    }
}
