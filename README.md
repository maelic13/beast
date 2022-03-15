# Beast
UCI compatible chess engine with neural network support
- alpha-beta pruning, quiescence search, delta pruning
- 50-moves rule, 3-fold repetition
- infinite analysis mode
- time management
- 3 types of heuristic (classic, neural network, random play)
- syzygy tablebases support

# How to run
Beast can be run
- from python console via src/beast.py
- using exe runner file

The exe file can be connected to your preferred GUI, communicating via UCI protocol, but has to be compiled from C# code.

## Prerequisites
Install python virtual environment via **venv.cmd** file.

## EXE
You can compile yourself from https://github.com/maelic13/beast_exe

The exe must be placed in beast repo, expecting following relative paths to exist
- ./venv/scripts/python.exe
- ./src/beast.py
