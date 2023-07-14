from os import environ

from chess import Board, Move
from cmd import Cmd
from queue import Queue
from threading import Thread, Event

from search import main as search_main, Node


# VARIABLES
engineName = 'Beast 1.01'
author = 'Miloslav Macurek'


# CLASSES
class GoParameters:
    def __init__(self):
        # position
        self.moves = ""
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
        self.moves = ""
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


class Options:
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
        self.modelFile = 'nets/bnn_2-100-2.h5'
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
            self.syzygyProbeLimit = int(value)
        elif option in ['quiescence', 'Quiescence']:
            if value in ['true', 'True', '1']:
                self.quiescence = True
            elif value in ['false', 'False', '0']:
                self.quiescence = False
        elif option in ['Heuristic', 'heuristic']:
            self.heuristic = value
            if value in ['random', 'Random']:
                go_params.depth = 1
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


class UciLoop(Cmd):
    prompt = ''

    def do_uci(self, arg):
        if opt.debug:
            f = open('log.txt', 'a')
            f.write('uci ')
            f.write(arg)
            f.write('\n')
            f.close()
        print('id name', engineName)
        print('id author', author)
        print()
        print('option name Threads type spin default',
              opt.threads, 'min 1 max 1')
        # time flexibility in ms so engine could make a move in time and did not lose on time
        print('option name TimeFlex type spin default',
              opt.timeFlex, 'min 0 max 1000')
        # types of search algorithms
        print('option name SearchAlgorithm type combo default',
              opt.searchAlgorithm, 'var AlphaBeta')
        print('option name Quiescence type check default',
              opt.quiescence)
        # path to syzygy tablebases
        print('option name SyzygyPath type string default',
              opt.syzygyPath)
        # probe limit for syzygy
        print('option name SyzygyProbeLimit type spin default',
              opt.syzygyProbeLimit, 'min 0 max 7')
        print('option name Syzygy50MoveRule type check default',
              opt.fiftyMoveRule)
        print('option name Heuristic type combo default',
              opt.heuristic, 'var Classic var NeuralNetwork var Random')
        print('option name Network type combo default',
              opt.network, 'var Regression var Classification')
        print('option name ModelFile type string default',
              opt.modelFile)
        print('uciok')

    def do_quit(self, arg):
        if opt.debug:
            f = open('log.txt', 'a')
            f.write('quit ')
            f.write(arg)
            f.write('\n')
            f.close()
        return True

    def do_setoption(self, arg):
        if opt.debug:
            f = open('log.txt', 'a')
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
            f = open('log.txt', 'a')
            f.write('isready ')
            f.write(arg)
            f.write('\n')
            f.close()
        print('readyok')

    def do_go(self, arg):
        if opt.debug:
            f = open('log.txt', 'a')
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
            f = open('log.txt', 'a')
            f.write('stop ')
            f.write(arg)
            f.write('\n')
            f.close()
        opt.flag.clear()

    def do_ucinewgame(self, arg):
        if opt.debug:
            f = open('log.txt', 'a')
            f.write('ucinewgame ')
            f.write(arg)
            f.write('\n')
            f.close()
        go_params.position = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

    def do_position(self, arg):
        if opt.debug:
            f = open('log.txt', 'a')
            f.write('position ')
            f.write(arg)
            f.write('\n')
            f.close()
        try:
            [command, arguments] = arg.split(' ', 1)
        except ValueError:
            command = arg
            arguments = None

        if command == 'startpos' and arguments:
            arguments = arguments.split()
            fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            moves = arguments[1:]
        elif command and not arguments:
            fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
            moves = None
        else:
            try:
                [fen, moves] = arguments.split(' moves ')
                moves = moves.split()
            except ValueError:
                fen = arguments
                moves = None

        go_params.root = get_root(fen, moves)
        if opt.debug:
            print(go_params.root.position)


# FUNCTIONS
def get_root(fen, moves):
    board = Board(fen)
    root = Node(fen)
    if moves is not None:
        for move in moves:
            fen = board.fen().split(' ')
            root.previous.append(' '.join(fen[:2]))
            board.push(Move.from_uci(move))
    root.position = board.fen()
    return root


def parse_params(go_params, string):
    run = True
    while run:
        if string == 'infinite':
            go_params.infinite = True
            break
        elif string == 'ponder':
            go_params.ponder = True
            break
        elif string == '':
            go_params.depth = 2
            break
        try:
            [command, param, string] = string.split(' ', 2)
        except ValueError:
            [command, param] = string.split(' ', 1)
            run = False

        if command == 'wtime':
            go_params.wtime = int(param)
        elif command == 'btime':
            go_params.btime = int(param)
        elif command == 'winc':
            go_params.winc = int(param)
        elif command == 'binc':
            go_params.binc = int(param)
        elif command == 'movestogo':
            go_params.movesToGo = int(param)
        elif command == 'depth':
            go_params.depth = int(param)
        elif command == 'nodes':
            go_params.nodes = int(param)
        elif command == 'mate':
            go_params.mate = int(param)
        elif command == 'movetime':
            go_params.movetime = int(param)


def go():
    while True:
        opt.flag.wait()
        go_params.reset()
        parse_params(go_params, task.get())
        search_main(go_params, opt)
        opt.flag.clear()


# MAIN + INITIALIZATIONS
if __name__ == '__main__':
    # do not log unnecessary tensorflow messages
    environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    # disable GPU for model evaluation even if available (slower than cpu for small beast nets)
    environ["CUDA_VISIBLE_DEVICES"] = "-1"

    opt = Options()						# global engine options
    go_params = GoParameters()			# parameters for current search
    task = Queue(maxsize=0)				# queue for communication between threads

    worker = Thread(target=go)			# worker thread
    worker.daemon = True				# stop when main thread stops

    print(engineName, 'by', author)

    worker.start()
    UciLoop().cmdloop()
