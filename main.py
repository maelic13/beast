from threading import Thread, Event, Timer
from queue import Queue
import board
import cmd

# VARIABLES
engineName = "Beast 0.05"
author = 'Maelic'

# CLASSES
class goParameters:
	def __init__(self):
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
		self.bestmove = None
		self.debug = False
		self.threads = 1
		self.fiftyMoveRule = True
		self.fullSearch = True
		self.pruningParam = 50
		self.timeFlex = 10
		self.searchAlgorithm = 'AlphaBeta'

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
			tree.setFiftyMoveRule(self.fiftyMoveRule)
		elif option in ['fullsearch', 'FullSearch']:
			if value in ['true', 'True', '1']:
				self.fullSearch = True
			elif value in ['false', 'False', '0']:
				self.fullSearch = False
		elif option in ['PruningParam', 'pruningparam']:
			self.pruningParam = value
		elif option in ['timeflex', 'TimeFlex']:
			self.timeFlex = value
		elif option in ['SearchAlgorithm', 'searchalgorithm']:
			self.searchAlgorithm = value

	def value(self, option):
		if option == "debug":
			return self.debug
		elif option == "threads":
			return self.threads

class uciLoop(cmd.Cmd):
	prompt = ''

	def do_uci(self, arg):
		print('id name', engineName)
		print('id author', author)
		print()
		print('option name Threads type spin default 1 min 1 max 1')
		print('option name FullSearch type check default true')						# search all possible moves without pruning
		print('option name PruningParam type spin default 50 min 0 max 1000')		# pruning parameter in cp
		print('option name TimeFlex type spin default 10 min 0 max 1000')			# time flexibility in ms so engine could make a move in time and did not lose on time
		print('option name SearchAlgorithm type combo default AlphaBeta var AlphaBeta var MCTS')	# types of search algorithms
		#print('option name SyzygyPath type string default <empty>')				# no TB support yet
		print('option name Syzygy50MoveRule type check default true')
		print('uciok')

	def do_quit(self, arg):
		return True

	def do_setoption(self, arg):
		command = arg.split()
		opt.set(command[1], command[3])
		if opt.debug:
			print(command[1], " = ", opt.value(command[1]))

	def do_debug(self, arg):
		opt.set('debug', arg)

	def do_isready(self, arg):
		print('readyok')

	def do_go(self, arg):
		task.put(arg)
		flag.set()

	def do_stop(self, arg):
		flag.clear()

	def do_ucinewgame(self, arg):
		tree.setPosition('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1', None)

	def do_position(self, arg):
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

		tree.setPosition(fen, moves)
		if opt.debug:
			print(tree.root.getBoard())

# FUNCTIONS
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
		flag.wait()
		goParams.reset()
		parseParams(goParams, task.get())
		tree.go(goParams, opt, flag)
		flag.clear()

# MAIN + INITIALIZATIONS
if __name__ == '__main__':
	opt = options()						# global engine options
	goParams = goParameters()			# parameters for current search
	task = Queue(maxsize=0)				# queue for communication between threads
	flag = Event()						# flag to start go function
	flag.clear()

	worker = Thread(target=go)			# worker thread
	worker.daemon = True				# stop when main thread stops

	tree = board.searchTree()			# main search tree
	print(engineName, 'by', author)

	worker.start()
	uciLoop().cmdloop()