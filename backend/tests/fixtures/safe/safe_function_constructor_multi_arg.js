function processInput(paramName) {
    new Function(paramName, "return 1;")(1);
}
