import java.io.IOException;

public class SafeProcessBuilderUnrelatedReceiver {
    public void runCommand(String command) throws IOException {
        Worker worker = new Worker(command);
        worker.start();
    }
}
