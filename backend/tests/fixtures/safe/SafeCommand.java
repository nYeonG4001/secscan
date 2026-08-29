import java.io.IOException;

public class SafeCommand {
    public void runFixedCommand() throws IOException {
        Runtime.getRuntime().exec("ls -la");
    }
}
