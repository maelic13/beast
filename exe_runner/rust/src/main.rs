use std::io;
use std::path::Path;
use std::process::Command;

fn main() {
    let dev_python_path = "./.venv_dev/scripts/python.exe";
    let default_python_path = "./.venv/scripts/python.exe";

    let python_exe_path;
    if Path::new(default_python_path).exists() {
        python_exe_path = default_python_path
    } else if Path::new(dev_python_path).exists() {
        python_exe_path = dev_python_path
    } else {
        println!("Python environment not found, use install.ps1 to setup first.");
        println!("Check that beast.exe is located in root folder next to the .venv.");
        println!("Press ENTER to exit...");
        let mut buffer = String::new();
        io::stdin().read_line(&mut buffer).expect("");
        return;
    }

    let status = Command::new(python_exe_path)
        .arg("./src/beast.py")
        .status()
        .expect("Failed to execute python script");

    std::process::exit(status.code().unwrap_or(1));
}
