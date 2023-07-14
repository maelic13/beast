from go_parameters import GoParameters
from options import Options


def get_time_for_move(go_parameters: GoParameters, options: Options, turn: bool) -> float:
    """
    Return time to take for calculating the next move for side to move in seconds, to be used
    in timer to reset flag and signal stop of calculation.
    :param go_parameters: parameters
    :param options: options
    :param turn: side to move
    :return: time in seconds
    """
    if go_parameters.infinite or go_parameters.ponder:
        return 0

    if go_parameters.movetime is not None:
        time = (go_parameters.movetime - options.timeFlex) / 1000
        return time

    if turn and go_parameters.wtime is not None:
        time = (0.2 * go_parameters.wtime - options.timeFlex) / 1000
        return time
    if not turn and go_parameters.btime is not None:
        time = (0.2 * go_parameters.btime - options.timeFlex) / 1000
        return time

    return 0
