import java.io.IOException;

public class SafeRuntimeExecSeparated {
    public void runCommand(String command) throws IOException {
        Runtime runtime = Runtime.getRuntime();
        runtime.exec(command);
    }
}
