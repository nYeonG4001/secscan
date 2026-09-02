import java.io.IOException;

public class SafeProcessBuilderShadowedCandidate {
    public void runCommand(String command) throws IOException {
        ProcessBuilder trusted = new ProcessBuilder("ls");
        ProcessBuilder tainted = new ProcessBuilder(command);
        trusted.start();
    }
}
