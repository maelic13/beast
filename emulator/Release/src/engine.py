import sys
import uci

print('Beast 0.1dev by Maelic')

# Delete previous logs into file
'''
file = open('log.txt', 'w')
file.write('')
file.close()
'''

# Main loop
while 1:
	# Input commands
	inputCommand = input()

	# Log into file
	'''
	file = open('log.txt', 'a+')
	file.write(inputCommand + '\n')
	file.close()
	'''
	uci.uci(inputCommand)