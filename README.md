# Beast
UCI compatible chess engine with neural network support
- alpha-beta pruning, quiescence search, delta pruning
- 50-moves rule, 3-fold repetition
- infinite analysis mode
- time management
- 4 types of heuristic (classic, neural network, legacy neural network, random play)
- syzygy tablebases support

# How to use
Beast can be run
- from python console via src/beast/beast.py
- using exe runner file

The exe runner can be connected to your preferred GUI, communicating via UCI protocol, 
but has to be compiled from C#, C++ or Rust code.

## Prerequisites
Install Python 3.12 from https://python.org/ website. 

Install python virtual environment using **pyproject.toml**.
