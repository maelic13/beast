import logging
logging.getLogger('tensorflow').setLevel(logging.FATAL)
import board
import heuristic
import nn_heuristic
from queue import Queue
import chess
from keras.models import load_model

#Various expand strategies    
def expand(tree, goParams, options):
    if tree.root.tablebasePosition and tree.depth >= 1:
        options.flag.clear()
        return
    # functions to find nodes to expand and put them into queue
    if options.expandType == 'Selective':
        selective(tree, tree.root, options.flag)
    elif options.expandType == 'Full':
        fullExpand(tree, tree.root, options.flag)
    elif options.expandType == 'FullPruned':
        prunedExpand(tree, tree.root, options)

    # expand nodes from queue and evaluate new nodes
    # later add worker processes
    executeExpand(tree, goParams, options)

def fullExpand(tree, current, flag):
    if not flag.is_set():
        return

    if current.children == [] and current.depth == tree.depth:
        if current.tablebasePosition and not current.parent == None:
            pass
        else:
            tree.expandQueue.put(current)
    else:   
        for each in current.children:
            fullExpand(tree, each, flag)

def prunedExpand(tree, current, options):
    # pruned expansion
    if not options.flag.is_set():
        return

    if current.children == [] and current.depth <= tree.depth:
        if current.tablebasePosition and not current.parent == None:
            pass
        else:
            tree.expandQueue.put(current)
    else:
        for i in range(options.pruningParam):
            try:
                prunedExpand(tree, current.children[i], options)
            except:
                return
        del(current.children[options.pruningParam:])

def selective(tree, current, flag):
    if not flag.is_set():
        return

    expandParam = [5, 3, 2, 1]
    
    if current.children == [] and current.depth <= tree.depth+1:
        if current.tablebasePosition and not current.parent == None:
            pass
        else:
            tree.expandQueue.put(current)
    else:
        if current.depth == 0 or current.depth == 1:
            for i in range(0,expandParam[0]):
                try:
                    selective(tree, current.children[i], flag)
                except:
                    return
            del(current.children[expandParam[0]:])
        elif current.depth == 2 or current.depth == 3:
            for i in range(0,expandParam[1]):
                try:
                    selective(tree, current.children[i], flag)
                except:
                    return
            del(current.children[expandParam[1]:])
        elif current.depth == 4 or current.depth == 5:
            for i in range(0,expandParam[2]):
                try:
                    selective(tree, current.children[i], flag)
                except:
                    return
            del(current.children[expandParam[2]:])
        else:
            for i in range(0,expandParam[3]):
                try:
                    selective(tree, current.children[i], flag)
                except:
                    return
            del(current.children[expandParam[3]:])

def executeExpand(tree, goParams, options):
    # load NN model if needed
    if options.nnHeuristic and options.nn_input_type == 'planes':
        model = load_model('net_planes.h5')
    elif options.nnHeuristic and options.nn_input_type == 'basic':
        model = load_model('net_basic.h5')

    # main execure expand loop
    while not tree.expandQueue.empty() and conditionsMet(tree.nodesCount, goParams.nodes, options.flag):
        current = tree.expandQueue.get()
        legalMoves = current.board.legal_moves
        
        for each in legalMoves:
            current.board.push(each)
            new = board.node(current.board.copy())
            current.board.pop()
            current.addChild(new)
            new.setParent(current)
            
            # choice of heuristic
            if options.nnHeuristic:
                nn_heuristic.nn_heuristic(new, options, model)
            else:
                heuristic.heuristic(new, options)

            new.depth = current.depth + 1
            if options.quiescence and (not isQuiet(tree, current, new, each)):          # pseudo quietscence search
                tree.expandQueue.put(new)
            tree.nodesCount += 1

        if current.board.turn:
            current.children = sorted(current.children, key=lambda child: child.eval, reverse=True)
        else:
            current.children = sorted(current.children, key=lambda child: child.eval)
    
    # dismiss model (to be sure)
    model = None

def conditionsMet(count, nodes, flag):
    if flag.is_set():
        if not nodes == None:
            if count < nodes:
                return True
            else:
                flag.clear()
                return False
        else:
            return True
    else:
        return False

def isQuiet(tree, current, new, move):
    ''' WAY TOO SLOW!
    if current.depth >= tree.depth:
        if current.board.is_capture(move) or new.board.is_check():
            if new.eval > 1000 or new.eval < -1000:
                return True
            else:
                return False
        else:
            return True
    else:
        return False
    '''
    # Check one forward after capture or check either one move or two as to end after opponent's move (also slow..)
    if (current.board.is_capture(move) or new.board.is_check()) and tree.depth > 0:
        if new.depth - tree.depth <= 1:
            return False
        elif new.board.turn != tree.root.board.turn:
            return False
        else:
            return True
    elif current.depth < tree.depth:
        return False
    else:
        if new.depth > tree.seldepth:
            tree.seldepth = new.depth
        return True

def main():
    pass

if __name__ == '__main__':
    main()