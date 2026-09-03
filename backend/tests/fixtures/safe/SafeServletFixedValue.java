import javax.servlet.http.HttpServletRequest;

public class SafeServletFixedValue {
    public void run(HttpServletRequest req) throws Exception {
        Runtime.getRuntime().exec("echo fixed");
    }
}
