#include <Python.h>

int main(int argc, char* argv[])
{

    Py_Initialize();
    PyRun_SimpleString("import sys");
    PyRun_SimpleString("sys.path.append(\"src\")");

    FILE* PScriptFile = fopen("src/main.py", "r");
    if (PScriptFile) {
        PyRun_SimpleFile(PScriptFile, "main.py");
        fclose(PScriptFile);
    }
    Py_Finalize();
    return 0;
}
