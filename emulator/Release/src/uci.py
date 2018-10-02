import sys

def uci(inputCommand):
	if inputCommand == "uci":
		print('id name Beast 0.1dev')
		print('id author Maelic')
		print()
		print('option name Threads type spin default 1 min 1 max 512')
		print('uciok')

	if inputCommand == "isready":
		print('readyok')

	if inputCommand == "quit":
		sys.exit()