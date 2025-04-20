# Beast
UCI compatible chess engine with neural network support
- alpha-beta pruning, quiescence search, delta pruning
- 50-moves rule, 3-fold repetition
- infinite analysis mode
- time management
- 4 types of heuristic (classic, neural network, legacy neural network, random play)
- syzygy tablebases support

# How to run
Beast can be run
- from python console via src/beast.py
- using exe runner file

The exe runner can be connected to your preferred GUI, communicating via UCI protocol, 
but has to be compiled from C#, C++ or Rust code.

## Prerequisites
Install python virtual environment via **install/install.ps1** file. Use help argument
to see options if you need dev environment.

## EXE
You can compile yourself from exe_runner\{language} subprojects.

Tested and working for Hiarcs Chess Explorer and Arena. Other GUIs likely work but not tested.

The exe must be placed in beast repo (root), expecting following relative paths to exist
- ./.venv(_dev)/scripts/python.exe
- ./src/beast.py
