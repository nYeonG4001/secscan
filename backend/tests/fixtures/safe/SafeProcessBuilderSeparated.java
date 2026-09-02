import java.io.IOException;

public class SafeProcessBuilderSeparated {
    public void runCommand(String command) throws IOException {
        ProcessBuilder pb = new ProcessBuilder(command);
        pb.start();
    }
}
