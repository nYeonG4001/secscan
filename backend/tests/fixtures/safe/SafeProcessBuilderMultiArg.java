import java.io.IOException;

public class SafeProcessBuilderMultiArg {
    public void runCommand(String command) throws IOException {
        new ProcessBuilder("sh", "-c", command).start();
    }
}
