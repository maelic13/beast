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

The exe file can be connected to your preferred GUI, communicating via UCI protocol, but has to be compiled from C# code.

For ease of use, the default version of Beast in master branch is non-neural network version to save you from installing tensorflow.
Should you wish to try neural network version, or train your own network, check out **nn_beast** branch. It will be kept up-to-date with
master.

For non-neural network Beast, you can use any up-to-date python 3 version. For neural network Beast, you will need tensorflow
and install its currently supported version of python.

## Prerequisites
Install python virtual environment via **venv.cmd** file.

## EXE
You can compile yourself from https://github.com/maelic13/BeastExe

Tested and working for Hiarcs Chess Explorer and Arena. For other GUIs, you have to test for yourself.

The exe must be placed in beast repo, expecting following relative paths to exist
- ./venv/scripts/python.exe
- ./src/beast.py
