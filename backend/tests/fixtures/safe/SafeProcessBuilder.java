import java.io.IOException;

public class SafeProcessBuilder {
    public void runFixedCommand() throws IOException {
        new ProcessBuilder("ls").start();
    }
}
