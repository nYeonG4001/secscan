import java.io.IOException;

public class CommandInjection {
    public void runCommand(String userInput) throws IOException {
        Runtime.getRuntime().exec(userInput);
    }
}
