from threading import Thread, Event
from queue import Queue
import board
import cmd

# VARIABLES
engineName = "Beast 0.04"
author = 'Maelic'

# CLASSES
class options():
	def __init__(self):
		self.bestmove = None
		self.debug = False
		self.threads = 1
		self.hash = 16
		self.fiftyMoveRule = True

	def set(self, option, value):
		if option == "debug" and value == "on":
			self.debug = True
		elif option == "debug" and value == "off":
			self.debug = False
		elif (option == "threads") and (int(value) < 32) and (int(value) > 0):
			self.threads = value
		elif (option == "hash") and (int(value) < 17000) and (int(value) > 0):
			self.hash = value
		elif option == 'Syzygy50MoveRule':
			if value in ['true', 'True', '1']:
				self.fiftyMoveRule = True
			elif value in ['false', 'False', '0']:
				self.fiftyMoveRule = False
			tree.setFiftyMoveRule(self.fiftyMoveRule)

	def value(self, option):
		if option == "debug":
			return self.debug
		elif option == "threads":
			return self.threads
		elif option == "hash":
			return self.hash

# FUNCTIONS
class uciLoop(cmd.Cmd):
	prompt = ''

	def do_uci(self, arg):
		print('id name', engineName)
		print('id author', author)
		print()
		print('option name Threads type spin default 1 min 1 max 1')
		#print('option name Hash type spin default 16 min 1 max 131072')	No need for hash for now
		print('option name Syzygy50MoveRule type check default true')
		print('uciok')

	def do_quit(self, arg):
		return True

	def do_setoption(self, arg):
		command = arg.split()
		opt.set(command[1], command[2])
		if opt.value("debug"):
			print(command[1], " = ", opt.value(command[1]))

	def do_isready(self, arg):
		print('readyok')

	def do_go(self, arg):
		task.put(arg.split())
		flag.set()

	def do_stop(self, arg):
		flag.clear()
		print('bestmove', tree.bestMove)


	def do_ucinewgame(self, arg):
		#delete tree
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

def go():
	while True:
		flag.wait()
		'''
		command = task.get()
		while flag.is_set():
			if command[0] == 'infinite':
				tree.go(0)
			if command[0] == 'depth':
				tree.go(int(command[1]))
				flag.clear()
		'''
		tree.go(2)
		flag.clear()

# MAIN + INITIALIZATIONS
if __name__ == '__main__':
	opt = options()
	task = Queue(maxsize=0)
	flag = Event()
	flag.clear()

	worker = Thread(target=go)
	worker.daemon = True

	tree = board.searchTree()
	print(engineName, 'by', author)

	worker.start()
	uciLoop().cmdloop()