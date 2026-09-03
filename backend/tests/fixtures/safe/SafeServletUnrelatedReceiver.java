public class SafeServletUnrelatedReceiver {
    public void run(UnrelatedRequest req) throws Exception {
        Runtime.getRuntime().exec(req.getParameter("cmd"));
    }
}

class UnrelatedRequest {
    public String getParameter(String name) {
        return "safe";
    }
}
