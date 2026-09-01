import java.sql.PreparedStatement;
import java.sql.SQLException;

public class SafeJdbcStatementSql {
    public void findUser(PreparedStatement statement, String userInput) throws SQLException {
        statement.setString(1, userInput);
        statement.executeQuery();
    }
}
