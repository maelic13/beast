using System;
using System.Diagnostics;
using System.IO;

namespace BeastExe;

internal static class Program
{
    public static void Main()
    {
        string pythonExePath;
        if (Directory.Exists("./.venv") && File.Exists("./.venv/scripts/python.exe"))
        {
            pythonExePath = "./.venv/scripts/python.exe";
        }
        else if (Directory.Exists("./.venv_dev") && File.Exists("./.venv_dev/scripts/python.exe"))
        {
            pythonExePath = "./.venv_dev/scripts/python.exe";
        }
        else
        {
            Console.WriteLine("Python environment not found, use install.ps1 to setup first.");
            Console.WriteLine("Check that beast.exe is located in root folder next to the .venv.");
            Console.WriteLine("Press ENTER to exit...");
            Console.ReadLine();
            return;
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
