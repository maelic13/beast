#include <iostream>
#include <string>
#include <filesystem>
#include <windows.h>

int main() {
    const std::string dev_python_path = "./.venv_dev/scripts/python.exe";
    const std::string default_python_path = "./.venv/scripts/python.exe";
    const std::string python_script_path = "./src/beast.py";

    std::string python_exe_path;
    if (std::filesystem::exists(default_python_path)) {
        python_exe_path = default_python_path;
    } else if (std::filesystem::exists(dev_python_path)) {
        python_exe_path = dev_python_path;
    } else {
        std::cout << "Python environment not found, use install.ps1 to setup first." << std::endl;
        std::cout << "Check that beast.exe is located in root folder next to the .venv." << std::endl;
        std::cout << "Press ENTER to exit..." << std::endl;
        std::cin.get();
        return EXIT_FAILURE;
    }

    STARTUPINFO si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    const std::string commandLine = "\"" + python_exe_path + "\" \"" + python_script_path + "\"";
    char *cmd = _strdup(commandLine.c_str());

    if (!CreateProcess(
            nullptr,
            cmd,
            nullptr,
            nullptr,
            FALSE,
            0,
            nullptr,
            nullptr,
            &si,
            &pi)
    ) {
        std::cerr << "CreateProcess failed (" << GetLastError() << ")" << std::endl;
        free(cmd);
        return 1;
    }

    WaitForSingleObject(pi.hProcess, INFINITE);

    DWORD exitCode;
    GetExitCodeProcess(pi.hProcess, &exitCode);

    CloseHandle(pi.hProcess);
    CloseHandle(pi.hThread);
    free(cmd);

    return exitCode;
}
