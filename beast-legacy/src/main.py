from os import environ
environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

import cmd
import search

from chess import Board, Move
from queue import Queue
from search import Node
from threading import Thread, Event

# VARIABLES
engineName = 'Beast 0.10'
author = 'M. Macurek'


# CLASSES
class goParameters:
    def __init__(self):
        # position
        self.root = Node('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')

        # time parameters
        self.wtime = None
        self.btime = None
        self.winc = None
        self.binc = None
        self.movesToGo = None
        self.movetime = None

        # depth parameters
        self.depth = None
        self.nodes = None
        self.mate = None

        # continuous parameters
        self.infinite = False
        self.ponder = False

    def reset(self):
        self.moves = ''
        self.wtime = None
        self.btime = None
        self.winc = None
        self.binc = None
        self.ponder = False
        self.movesToGo = None
        self.depth = None
        self.nodes = None
        self.mate = None
        self.movetime = None
        self.infinite = False


class options():
    def __init__(self):
        self.debug = False						# debug option
        self.threads = 1						# number of threads
        self.fiftyMoveRule = True				# whether to play with 50-move rule or not
        self.syzygyPath = '<empty>'				# path to syzygy tablebases
        self.syzygyProbeLimit = 6				# probe limit for syzygy tablebases
        self.timeFlex = 10						# time flex for time management
        self.searchAlgorithm = 'AlphaBeta'		# search algorithm
        self.flag = Event()						# flag to start go function
        self.quiescence = True
        self.heuristic = 'Classic'				# type of heuristic
        self.network = 'Regression'				# type of neural network system
        self.modelFile = '<default>'
        self.model = None

    def set(self, option, value):
        if option in ['debug', 'Debug'] and value in ['on', 'On']:
            self.debug = True
        elif option in ['debug', 'Debug'] and value in ['off', 'Off']:
            self.debug = False
        elif (option in ["threads", 'Threads']) and (int(value) < 32) and (int(value) > 0):
            self.threads = value
        elif option == 'Syzygy50MoveRule':
            if value in ['true', 'True', '1']:
                self.fiftyMoveRule = True
            elif value in ['false', 'False', '0']:
                self.fiftyMoveRule = False
        elif option in ['timeflex', 'TimeFlex']:
            self.timeFlex = value
        elif option in ['SearchAlgorithm', 'searchalgorithm']:
            self.searchAlgorithm = value
        elif option in ['SyzygyPath', 'syzzygypath']:
            self.syzygyPath = value.replace('\\', '/')
        elif option in ['SyzygyProbeLimit', 'syzygyprobelimit']:
            self.syzygyProbeLimit = value
        elif option in ['quiescence', 'Quiescence']:
            if value in ['true', 'True', '1']:
                self.quiescence = True
            elif value in ['false', 'False', '0']:
                self.quiescence = False
        elif option in ['Heuristic', 'heuristic']:
            self.heuristic = value
            if value in ['random', 'Random']:
                goParams.depth = 1
        elif option in ['network', 'Network']:
            self.network = value
        elif option in ['modelfile', 'ModelFile']:
            self.modelFile = value.replace('\\', '/')

    def value(self, option):
        if option == "debug":
            return self.debug
        elif option == "threads":
            return self.threads
        elif option in ['SyzygyPath', 'syzygypath']:
            return self.syzygyPath
        elif option in ['SyzygyProbeLimit', 'syzygyprobelimit']:
            return self.syzygyProbeLimit
        elif option in ['quiescence', 'Quiescence']:
            return self.quiescence
        elif option in ['heuristic', 'Heuristic']:
            return self.heuristic
        elif option in ['Network', 'network']:
            return self.network
        elif option in ['modelfile', 'ModelFile']:
            return self.modelFile


class uciLoop(cmd.Cmd):
    prompt = ''

    #f = open('log.txt','w').close()

    def do_uci(self, arg):
        if opt.debug:
            f = open('log.txt','a')
            f.write('uci ')
            f.write(arg)
            f.write('\n')
            f.close()
        print('id name', engineName)
        print('id author', author)
        print()
        print('option name Threads type spin default', opt.threads,'min 1 max 1')
        print('option name TimeFlex type spin default', opt.timeFlex,'min 0 max 1000')										# time flexibility in ms so engine could make a move in time and did not lose on time
        print('option name SearchAlgorithm type combo default', opt.searchAlgorithm,'var AlphaBeta')# var MCTS')			# types of search algorithms
        print('option name Quiescence type check default', opt.quiescence)
        print('option name SyzygyPath type string default', opt.syzygyPath)													# path to syzygy tablebases
        print('option name SyzygyProbeLimit type spin default', opt.syzygyProbeLimit,'min 0 max 7')							# probe limit for syzygy
        print('option name Syzygy50MoveRule type check default', opt.fiftyMoveRule)
        print('option name Heuristic type combo default', opt.heuristic,'var Classic var NeuralNetwork var Random')
        print('option name Network type combo default', opt.network,'var Regression var Classification')
        print('option name ModelFile type string default', opt.modelFile)
        print('uciok')

    def do_quit(self, arg):
        if opt.debug:
            f = open('log.txt','a')
            f.write('quit ')
            f.write(arg)
            f.write('\n')
            f.close()
        return True

    def do_setoption(self, arg):
        if opt.debug:
            f = open('log.txt','a')
            f.write('setoption ')
            f.write(arg)
            f.write('\n')
            f.close()
        command = arg.split()
        opt.set(command[1], command[3])
        if opt.debug:
            print(command[1], " = ", opt.value(command[1]))

    def do_debug(self, arg):
        opt.set('debug', arg)

    def do_isready(self, arg):
        if opt.debug:
            f = open('log.txt','a')
            f.write('isready ')
            f.write(arg)
            f.write('\n')
            f.close()
        print('readyok')

    def do_go(self, arg):
        if opt.debug:
            f = open('log.txt','a')
            f.write('go ')
            f.write(arg)
            f.write('\n')
            f.close()
        if arg.startswith('ponder'):
            return
        task.put(arg)
        opt.flag.set()

    def do_stop(self, arg):
        if opt.debug:
            f = open('log.txt','a')
            f.write('stop ')
            f.write(arg)
            f.write('\n')
            f.close()
        opt.flag.clear()

    def do_ucinewgame(self, arg):
        if opt.debug:
            f = open('log.txt','a')
            f.write('ucinewgame ')
            f.write(arg)
            f.write('\n')
            f.close()
        goParams.position = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

    def do_position(self, arg):
        if opt.debug:
            f = open('log.txt','a')
            f.write('position ')
            f.write(arg)
            f.write('\n')
            f.close()
        try:
            [command, arguments] = arg.split(' ', 1)
        except:
            command = arg
            arguments = None

        if command == 'startpos':
            try:
                arguments = arguments.split()
                fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
                moves = arguments[1:]
            except:
                fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
                moves = None
        elif command == 'fen':
            try:
                [fen, moves] = arguments.split(' moves ')
                moves = moves.split()
            except:
                fen = arguments
                moves = None

        goParams.root = get_root(fen, moves)
        if opt.debug:
            print(goParams.root.position)


# FUNCTIONS
def get_root(fen, moves):
    board = Board(fen)
    root = Node(fen)
    if not moves == None:
        for move in moves:
            fen = board.fen().split(' ')
            root.previous.append(' '.join(fen[:2]))
            board.push(Move.from_uci(move))
    root.position = board.fen()
    return root


def parseParams(goParams, string):
    run = True
    while run:
        if string == 'infinite':
            goParams.infinite = True
            break
        elif string == 'ponder':
            goParams.ponder = True
            break
        elif string == '':
            goParams.depth = 2
            break
        try:
            [command, param, string] = string.split(' ', 2)
        except:
            [command, param] = string.split(' ', 1)
            run = False

        if command == 'wtime':
            goParams.wtime = int(param)
        elif command == 'btime':
            goParams.btime = int(param)
        elif command == 'winc':
            goParams.winc = int(param)
        elif command == 'binc':
            goParams.binc = int(param)
        elif command == 'movestogo':
            goParams.movesToGo = int(param)
        elif command == 'depth':
            goParams.depth = int(param)
        elif command == 'nodes':
            goParams.nodes = int(param)
        elif command == 'mate':
            goParams.mate = int(param)
        elif command == 'movetime':
            goParams.movetime = int(param)


def go():
    while True:
        opt.flag.wait()
        goParams.reset()
        parseParams(goParams, task.get())
        search.main(goParams, opt)
        opt.flag.clear()


# MAIN + INITIALIZATIONS
if __name__ == '__main__':
    opt = options()						# global engine options
    goParams = goParameters()			# parameters for current search
    task = Queue(maxsize=0)				# queue for communication between threads

    worker = Thread(target=go)			# worker thread
    worker.daemon = True				# stop when main thread stops

    print(engineName, 'by', author)

    worker.start()
    uciLoop().cmdloop()
