import sys
import time
from threading import Thread, Event
from queue import Queue

# VARIABLES
engineName = "Beast 0.02"

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
	while True:
		command = analyseCommand(input())
		# Log into file
		'''
		file = open('log.txt', 'a+')
		file.write(command + '\n')
		fil.close()
		'''
		if command[0] == "quit":
			sys.exit()

		if command[0] == "uci":
			print('id name', engineName)
			print('id author Maelic')
			print()
			print('option name Threads type spin default 1 min 1 max 32')
			print('option name Hash type spin default 16 min 1 max 131072')
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

		if command[0] == "ucinewgame":
			continue


def analyseCommand(inputCommand):
	command = inputCommand.split()
	return command

def go():
	while True:
		flag.wait()
		command = task.get()
		while flag.is_set():
			print(command)
			time.sleep(1)

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

	print(engineName, 'by Maelic')
	tasks = Queue(maxsize=0)

	worker.start()

	uciLoop()