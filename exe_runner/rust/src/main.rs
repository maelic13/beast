use std::path::Path;
use std::process::Command;

fn main() {
    let dev_python_path = "./.venv_dev/scripts/python.exe";
    let default_python_path = "./.venv/scripts/python.exe";

    let python_exe_path = if Path::new(dev_python_path).exists() {
        dev_python_path
    } else {
        default_python_path
    };

    let status = Command::new(python_exe_path)
        .arg("./src/beast.py")
        .status()
        .expect("Failed to execute python script");

    std::process::exit(status.code().unwrap_or(1));
}
