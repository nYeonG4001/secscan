public class ProcessBuilderServletJakarta {
    public void startProcess(jakarta.servlet.http.HttpServletRequest req) throws Exception {
        new ProcessBuilder(req.getPathInfo()).start();
    }
}
