import java.sql.Connection;
import java.sql.Statement;

public class JdbcStatementSqlServletJavax {
    public void execute(Connection conn, javax.servlet.http.HttpServletRequest req) throws Exception {
        Statement stmt = conn.createStatement();
        stmt.executeQuery(req.getHeader("X-Query"));
    }
}
