import javax.servlet.http.HttpServletRequest;

public class ServletLocalPropagation {
    public void run(HttpServletRequest req) throws Exception {
        String cmd = req.getParameter("cmd");
        Runtime.getRuntime().exec(cmd);
    }
}
