import java.io.IOException;

public class ProcessBuilderSeparated {
    public void runCommand(String command) throws IOException {
        ProcessBuilder builder = new ProcessBuilder(command);
        builder.start();
    }
}
