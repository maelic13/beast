# Beast

UCI-compatible chess engine with classical and neural network evaluation.

Features:
- alpha-beta pruning, quiescence search, delta pruning
- 50-move rule and threefold repetition handling
- infinite analysis mode
- time management
- three heuristic types: classical, neural network, random
- Syzygy tablebase support

## Releases

- [Latest release](https://github.com/maelic13/beast/releases/latest)
- [All releases](https://github.com/maelic13/beast/releases)

Release assets include:
- standalone executables for Windows (x64, arm64), macOS (arm64) and Linux (x64, arm64).
- the latest bundled neural-network model as a separate `.onnx` asset

## macOS permissions
To run on macOS, use these two command to allow the executable to run
1. ```xattr -d com.apple.quarantine <path_to_executable>```
2. ```chmod +x <path_to_executable>```

## Requirements

- Python 3.12 or newer

Beast targets Python `>=3.12`. You do not need to use exactly Python 3.12;
newer supported Python versions work too as long as the dependencies for your platform are available.

## Install And Run From Python

1. Create and activate a Python virtual environment, or use a suitable system Python.
2. Install Beast:

```bash
pip install .
```

3. Start the engine:

```bash
beast
```

## Build A Local Executable

1. Create and activate a Python virtual environment.
2. Install build dependencies:

```bash
pip install ".[build]"
```

3. Build the executable:

```bash
pyinstaller --clean --onefile --optimize=2 --noupx --name beast src/beast_chess/main.py
```

The executable will be created in the `dist` folder as `beast` on macOS/Linux or `beast.exe` on Windows.

## Neural Network Evaluation

Beast uses classical evaluation by default.

Neural-network evaluation is available as an optional mode. Beast expects the model file to be placed:
- running from the source code: the repository root
- running the built executable: the same folder as the executable file

If the selected neural-network model cannot be found when a search starts, 
Beast reports the problem and waits for more commands.

### Enable Neural Network Mode

To use neural-network evaluation:

1. Download the latest Beast release assets, including the `.onnx` model file.
2. Place the model file in the same folder as the Beast executable or in the project root if running from source.
3. In your GUI or UCI console, set:

```text
setoption name Heuristic value neural_network
```

You can also point `ModelFile` to another compatible `.onnx` file:

```text
setoption name ModelFile value <path to your model file>
```

## UCI Options

Relevant UCI options include:
- `Heuristic`: `classical`, `neural_network`, or `random`
- `ModelFile`: path to the ONNX model to use for neural-network evaluation
- `SyzygyPath`
- `Syzygy50MoveRule`
- `SyzygyProbeLimit`
- `Threads`

## Train Your Own Neural Network

Neural-network training and model-management tooling live in a separate repository:

- [net_trainer](https://github.com/maelic13/net_trainer)

## License

GPL-3.0-or-later. See [LICENSE](LICENSE).
