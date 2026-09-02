function processInput(userCode) {
    new Function("arg", userCode)("value");
}
