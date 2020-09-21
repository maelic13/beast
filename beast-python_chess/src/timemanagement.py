def timeForMove(goParams, options, turn):
    if goParams.winc == None:
        goParams.winc = 0
        goParams.binc = 0

    if goParams.infinite or goParams.ponder or (goParams.depth != None) or (goParams.nodes != None):
        return 0
    if not (goParams.movetime == None):
        time = (goParams.movetime - options.timeFlex)/1000
        return time
    else:
        if turn:
            time = (0.2*goParams.wtime - options.timeFlex)/1000
            return time
        else:
            time = (0.2*goParams.btime - options.timeFlex)/1000
            return time