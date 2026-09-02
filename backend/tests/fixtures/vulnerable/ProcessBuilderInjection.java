import java.io.IOException;

public class ProcessBuilderInjection {
    public void runCommand(String command) throws IOException {
        new ProcessBuilder(command).start();
    }
}
