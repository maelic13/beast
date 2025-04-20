using System.Diagnostics;
using System.IO;

namespace BeastExe;

internal static class Program
{
    public static void Main()
    {
        string pythonExePath;
        if (Directory.Exists("./.venv_dev") && File.Exists("./.venv_dev/scripts/python.exe"))
        {
            pythonExePath = "./.venv_dev/scripts/python.exe";
        }
        else
        {
            pythonExePath = "./.venv/scripts/python.exe";
        }
            
        var process = new Process {
            StartInfo = new ProcessStartInfo {
                FileName = pythonExePath,
                Arguments = "./src/beast.py",
                UseShellExecute = false
            }
        };
        process.Start();
        process.WaitForExit();
    }
}
