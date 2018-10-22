import sys
import time
from threading import Thread, Event
from queue import Queue
import board
import chess

# VARIABLES
engineName = "Beast 0.03"
author = 'Maelic'

# CLASSES
class options():
	def __init__(self):
		self.position = None
		self.bestmove = None
		self.debug = False
		self.threads = 1
		self.hash = 16

	def set(self, option, value):
		if option == "debug" and value == "on":
			self.debug = True
		elif option == "debug" and value == "off":
			self.debug = False
		elif (option == "threads") and (int(value) < 32) and (int(value) > 0):
			self.threads = value
		elif (option == "hash") and (int(value) < 17000) and (int(value) > 0):
			self.hash = value

	def value(self, option):
		if option == "debug":
			return self.debug
		elif option == "threads":
			return self.threads
		elif option == "hash":
			return self.hash

# FUNCTIONS
def uciLoop():
	run = True
	while run:
		inp = input()
		command = analyseCommand(inp)

		# Log into file		
		file = open('log.txt', 'a+')
		file.write(inp + '\n')
		file.close()
		
		if command[0] == "quit":
			run = False

		if command[0] == "uci":
			print('id name', engineName)
			print('id author', author)
			print()
			print('option name Threads type spin default 1 min 1 max 1')
			#print('option name Hash type spin default 16 min 1 max 131072')	No need for hash for now
			print('uciok')

		if command[0] == "setoption":
			opt.set(command[2], command[3])
			if opt.value("debug"):
				print(command[2], " = ", opt.value(command[2]))

		if command[0] == "isready":
			print('readyok')

		if command[0] == "go":
			task.put(command[1:])
			flag.set()
		
		if command[0] == "stop":
			flag.clear()
			print('bestmove', tree.bestMove)

		if command[0] == "ucinewgame":
			continue

		if command[0] == "position":
			if command[1] == "startpos":
				tree.setPosition('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
			elif command[1] == "startpos" and command[2] == "moves" and len(command) > 2:
				tree.setPosition('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')
				for i in range(3,len(command)):
					tree.root.board.push(chess.Move.from_uci(command[i]))
			


def analyseCommand(inputCommand):
	command = inputCommand.split()
	return command

def go():
	while True:
		flag.wait()
		command = task.get()
		while flag.is_set():
			if command[0] == 'infinite':
				tree.go(0)
			if command[0] == 'depth':
				tree.go(int(command[1]))
				flag.clear()


# MAIN + INITIALIZATIONS
if __name__ == '__main__':

	# Delete previous logs into file
	file = open('log.txt', 'w')
	file.write('')
	file.close()

	opt = options()
	task = Queue(maxsize=0)
	flag = Event()
	flag.clear()
	worker = Thread(target=go)
	worker.daemon = True
	tree = board.searchTree()
	tree.setPosition('rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1')

	print(engineName, 'by', author)
	tasks = Queue(maxsize=0)

	worker.start()

	uciLoop()