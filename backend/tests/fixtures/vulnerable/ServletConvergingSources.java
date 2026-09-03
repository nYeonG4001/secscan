import javax.servlet.http.HttpServletRequest;

public class ServletConvergingSources {
    public void run(HttpServletRequest req, String userParam) throws Exception {
        Runtime.getRuntime().exec(userParam + req.getParameter("cmd"));
    }
}
