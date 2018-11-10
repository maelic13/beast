import board
import heuristic
from queue import Queue
#Various expand strategies
    
def expand(tree, goParams, options, flag):
    # functions to find nodes to expand and put them into queue
    if options.fullSearch:
        fullExpand(tree, tree.root, goParams, flag)
    else:
        prunedExpand(tree, tree.root, goParams, flag)

    # expand nodes from queue and evaluate new nodes
    # later add worker processes
    executeExpand(tree, goParams, flag)

def fullExpand(tree, current, goParams, flag):
    if not flag.is_set():
        return

    if current.children == []:
        tree.expandQueue.put(current)
    else:   
        for each in current.children:
            fullExpand(tree,each,goParams,flag)

def prunedExpand(tree, current, goParams, flag):
    # pruned expansion
    random = 1

def executeExpand(tree, goParams, flag):
    while not tree.expandQueue.empty() and flag.is_set() and conditionsMet(tree.nodesCount, goParams.nodes):
        current = tree.expandQueue.get()
        legalMoves = current.getBoard().legal_moves
        for each in legalMoves:
            current.board.push(each)
            new = board.node(current.board.copy())
            current.board.pop()
            current.addChild(new)
            new.setParent(current)
            heuristic.heuristic(new, tree.fiftyMoveRule)
            tree.nodesCount += 1

def conditionsMet(count, nodes):
    if not nodes == None:
        if count < nodes:
            return True
        else:
            return False
    else:
        return True