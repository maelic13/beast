def timeForMove(goParams, options, turn):
    if goParams.winc is None:
        goParams.winc = 0
        goParams.binc = 0

    if goParams.infinite or goParams.ponder or (goParams.depth is not None) \
            or (goParams.nodes is not None):
        return 0
    if goParams.movetime is not None:
        time = (goParams.movetime - options.timeFlex) / 1000
        return time
    else:
        if turn:
            time = (0.2 * goParams.wtime - options.timeFlex) / 1000
            return time
        else:
            time = (0.2 * goParams.btime - options.timeFlex) / 1000
            return time
