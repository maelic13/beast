# Beast
UCI compatible chess engine with neural network support
- alpha-beta pruning, quiescence search, delta pruning
- 50-moves rule, 3-fold repetition
- infinite analysis mode
- time management
- Three types of heuristic (classic, neural network, random play)
- syzygy tablebases support

# How to use

## Use latest released executable
- [Latest release](https://github.com/maelic13/beast/releases/latest)  
- [All releases](https://github.com/maelic13/beast/releases)

## Chess engine in the Python console
1. Create a Python 3.12 virtual environment (or use system Python)
2. Activate the environment
3. ```pip install .```
4. ```beast```

## Build latest dev chess engine executable
1. Create a Python 3.12 virtual environment (or use system Python)
2. Activate the environment
3. ```pip install .[build]```
4. ```pyinstaller --clean --onefile --name beast --optimize=2 src/beast_chess/main.py```
5. Executable will be created in /dist

## Train your own neural network for Beast
1. Create a Python 3.12 virtual environment (or use system Python)
2. Activate the environment
3. ```pip install .[dev]```, or ```pip install .[dev,cuda]```
for systems with CUDA capable GPU. On windows, you have to use WSL2,
see [install tensorflow](https://www.tensorflow.org/install/pip#windows-wsl2).
4. Use notebooks with this environment, modify to your liking
