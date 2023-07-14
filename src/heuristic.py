import numpy as np

import chess
import chess.syzygy
from random import uniform, randrange


# VARIABLES
# Piece values
pawn = 100
knight = 350
bishop = 350
rook = 525
queen = 1000

# Parameter weights for bonus eval
pawnRankW = 7
pawnFileW = 5
pawnCenterW = 5
pawnDistanceW = 5

knightCenterW = 7
knightDistanceW = 8

bishopCenterW = 5
bishopDistanceW = 8

rookCenterW = 8
rookDistanceW = 5

queenCenterW = 2
queenDistanceW = 8

kingCenterWvalue = 8
kingDistanceW = 5


# FUNCTIONS
def heuristic(fen, options):
    board = chess.Board(fen)

    # special eval conditions
    if board.is_game_over():
        if board.is_checkmate():
            return -25500
        else:
            return 0

    if options.fiftyMoveRule and int(fen.split(' ')[4]) >= 100:
        return 0

    # normal eval conditions
    else:
        eval = 0
        map = board.piece_map()

        # tablebase probing
        if len(map) <= options.syzygyProbeLimit and options.syzygyPath != '<empty>':
            with chess.syzygy.open_tablebase(
                    options.syzygyPath, load_wdl=True, max_fds=128) as tablebase:
                wdl = tablebase.get_wdl(board)
                if wdl is not None:
                    if options.fiftyMoveRule and wdl == -2:
                        eval = -12800
                    elif options.fiftyMoveRule and wdl == 2:
                        eval = 12800
                    elif not options.fiftyMoveRule and wdl == 1:
                        eval = 12800
                    elif not options.fiftyMoveRule and wdl == -1:
                        eval = -12800
                    else:
                        return 0
            tablebase.close()

        # structures for piece placement
        wPawns = []
        bPawns = []
        wKnights = []
        bKnights = []
        wBishops = []
        bBishops = []
        wRooks = []
        bRooks = []
        wQueens = []
        bQueens = []
        wKing = []
        bKing = []

        # fill structures
        for each in map:
            if board.piece_at(each) == chess.Piece(chess.PAWN, chess.WHITE):
                wPawns.append(each)
            if board.piece_at(each) == chess.Piece(chess.PAWN, chess.BLACK):
                bPawns.append(each)
            if board.piece_at(each) == chess.Piece(chess.KNIGHT, chess.WHITE):
                wKnights.append(each)
            if board.piece_at(each) == chess.Piece(chess.KNIGHT, chess.BLACK):
                bKnights.append(each)
            if board.piece_at(each) == chess.Piece(chess.BISHOP, chess.WHITE):
                wBishops.append(each)
            if board.piece_at(each) == chess.Piece(chess.BISHOP, chess.BLACK):
                bBishops.append(each)
            if board.piece_at(each) == chess.Piece(chess.ROOK, chess.WHITE):
                wRooks.append(each)
            if board.piece_at(each) == chess.Piece(chess.ROOK, chess.BLACK):
                bRooks.append(each)
            if board.piece_at(each) == chess.Piece(chess.QUEEN, chess.WHITE):
                wQueens.append(each)
            if board.piece_at(each) == chess.Piece(chess.QUEEN, chess.BLACK):
                bQueens.append(each)
            if board.piece_at(each) == chess.Piece(chess.KING, chess.WHITE):
                wKing.append(each)
            if board.piece_at(each) == chess.Piece(chess.KING, chess.BLACK):
                bKing.append(each)

        # Initial eval - adding value of pieces on board
        tab_eval = eval
        eval = (len(wPawns) * pawn - len(bPawns) * pawn
                + len(wKnights) * knight - len(bKnights) * knight
                + len(wBishops) * bishop - len(bBishops) * bishop
                + len(wRooks) * rook - len(bRooks) * rook
                + len(wQueens) * queen - len(bQueens) * queen)

        # BUNUSES
        # Pawns
        wpBonus = pawnBonus(wPawns, bKing, True)
        bpBonus = pawnBonus(bPawns, wKing, False)

        # Knights
        wkBonus = knightBonus(wKnights, bKing, True)
        bkBonus = knightBonus(bKnights, wKing, False)

        # Bishops
        wbBonus = bishopBonus(wBishops, bKing, True)
        bbBonus = bishopBonus(bBishops, wKing, False)

        # Rooks
        wrBonus = rookBonus(wRooks, bKing, True)
        brBonus = rookBonus(bRooks, wKing, False)

        # Queens
        wqBonus = queenBonus(wQueens, bKing, True)
        bqBonus = queenBonus(bQueens, wKing, False)

        # Kings
        wkingBonus = kingBonus(wKing, bKing, bQueens == [])
        bkingBonus = kingBonus(bKing, wKing, wQueens == [])

        # Add bonuses to eval
        eval += (wpBonus - bpBonus
                 + wkBonus - bkBonus
                 + wbBonus - bbBonus
                 + wrBonus - brBonus
                 + wqBonus - bqBonus
                 + wkingBonus - bkingBonus)
        # Assign eval to node
        if board.turn:
            return int(eval) + tab_eval
        else:
            return -int(eval) + tab_eval


def pawnBonus(pawns, king, color):
    pBonus = 0
    for each in pawns:
        # rank bonus -> the further the pawn, the more of a bonus
        if color:
            pBonus += (int(each / 8) - 1) * pawnRankW
        else:
            pBonus += (6 - int(each / 8)) * pawnRankW
        # file decrement -> central files take nothing, the closer to rim, the less pawn's value
        if each % 8 < 3:
            pBonus -= (3 - each % 8) * pawnFileW
        elif each % 8 > 4:
            pBonus -= (each % 8 - 4) * pawnFileW
        else:
            pass

        # occupying center bonus
        if int(each / 8) in range(3, 5) and each % 8 in range(3, 5):
            pBonus += pawnCenterW
        if int(each / 8) in range(2, 6) and each % 8 in range(2, 6):
            pBonus += pawnCenterW
        if int(each / 8) in range(1, 7) and each % 8 in range(1, 7):
            pBonus += pawnCenterW

        # distance from king bonus
        distance = abs(int(each / 8) - int(king[0] / 8)) + abs(each % 8 - king[0] % 8)
        pBonus += 14 / distance * pawnDistanceW - pawnDistanceW

    return pBonus


def knightBonus(knights, king, _color):
    kBonus = 0
    for each in knights:
        # occupying center bonus
        if int(each / 8) in range(3, 5) and each % 8 in range(3, 5):
            kBonus += knightCenterW
        if int(each / 8) in range(2, 6) and each % 8 in range(2, 6):
            kBonus += knightCenterW
        if int(each / 8) in range(1, 7) and each % 8 in range(1, 7):
            kBonus += knightCenterW

        # distance from king bonus
        distance = abs(int(each / 8) - int(king[0] / 8)) + abs(each % 8 - king[0] % 8)
        kBonus += 14 / distance * knightDistanceW - knightDistanceW
    return kBonus


def bishopBonus(bishops, king, _color):
    bBonus = 0
    for each in bishops:
        # occupying center bonus
        if int(each / 8) in range(3, 5) and each % 8 in range(3, 5):
            bBonus += bishopCenterW
        if int(each / 8) in range(2, 6) and each % 8 in range(2, 6):
            bBonus += bishopCenterW
        if int(each / 8) in range(1, 7) and each % 8 in range(1, 7):
            bBonus += bishopCenterW

        # distance from king bonus
        distance = abs(int(each / 8) - int(king[0] / 8)) + abs(each % 8 - king[0] % 8)
        bBonus += 14 / distance * bishopDistanceW - bishopDistanceW
    return bBonus


def rookBonus(rooks, king, _color):
    rBonus = 0
    for each in rooks:
        # occupying center files bonus
        if each % 8 in range(3, 5):
            rBonus += rookCenterW
        if each % 8 in range(2, 6):
            rBonus += rookCenterW
        if each % 8 in range(1, 7):
            rBonus += rookCenterW

        # distance from king bonus
        distance = abs(int(each / 8) - int(king[0] / 8)) + abs(each % 8 - king[0] % 8)
        rBonus += 14 / distance * rookDistanceW - rookDistanceW
    return rBonus


def queenBonus(queens, king, _color):
    qBonus = 0
    for each in queens:
        # occupying center bonus
        if int(each / 8) in range(3, 5) and each % 8 in range(3, 5):
            qBonus += queenCenterW
        if int(each / 8) in range(2, 6) and each % 8 in range(2, 6):
            qBonus += queenCenterW
        if int(each / 8) in range(1, 7) and each % 8 in range(1, 7):
            qBonus += queenCenterW

        # distance from king bonus
        distance = abs(int(each / 8) - int(king[0] / 8)) + abs(each % 8 - king[0] % 8)
        qBonus += 14 / distance * queenDistanceW - queenDistanceW
    return qBonus


def kingBonus(king, oponentKing, noQueen):
    kingBonus = 0
    if noQueen:
        kingCenterW = kingCenterWvalue
    else:
        kingCenterW = -kingCenterWvalue

    for each in king:
        # occupying center bonus
        if int(each / 8) in range(3, 5) and each % 8 in range(3, 5):
            kingBonus += kingCenterW
        if int(each / 8) in range(2, 6) and each % 8 in range(2, 6):
            kingBonus += kingCenterW
        if int(each / 8) in range(1, 7) and each % 8 in range(1, 7):
            kingBonus += kingCenterW

        # distance from king bonus
        distance = abs(int(each / 8) - int(oponentKing[0] / 8)) + abs(each % 8 - oponentKing[0] % 8)
        kingBonus += 14 / distance * kingDistanceW - kingDistanceW
    return kingBonus


def fen_to_input(fen):
    fen = fen.split(' ')
    inp = np.zeros((7, 8, 8), dtype=int)

    # plane who's to move
    if fen[1] == 'w':
        inp[6, ] = np.ones((8, 8), dtype=int)
    else:
        inp[6, ] = -np.ones((8, 8), dtype=int)

    # parse board
    fen = fen[0].split('/')
    row = 0
    for each in fen:
        col = 0
        for sign in each:
            if sign == 'p':
                inp[0, row, col] = -1
            elif sign == 'P':
                inp[0, row, col] = 1
            elif sign == 'n':
                inp[1, row, col] = -1
            elif sign == 'N':
                inp[1, row, col] = 1
            elif sign == 'b':
                inp[2, row, col] = -1
            elif sign == 'B':
                inp[2, row, col] = 1
            elif sign == 'r':
                inp[3, row, col] = -1
            elif sign == 'R':
                inp[3, row, col] = 1
            elif sign == 'q':
                inp[4, row, col] = -1
            elif sign == 'Q':
                inp[4, row, col] = 1
            elif sign == 'k':
                inp[5, row, col] = -1
            elif sign == 'K':
                inp[5, row, col] = 1
            else:
                col += int(sign) - 1
            col += 1
        row += 1

    return inp


def fen_to_pieces_input(fen):
    board = chess.Board(fen)
    input = np.zeros((8, 8, 7), dtype=int)

    for i in range(0, 64):
        if board.piece_at(i) == chess.Piece(chess.PAWN, chess.WHITE):
            input[i // 8, i % 8, 0] = 1
        elif board.piece_at(i) == chess.Piece(chess.PAWN, chess.BLACK):
            input[i // 8, i % 8, 0] = -1
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.WHITE):
            input[i // 8, i % 8, 1] = 1
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.BLACK):
            input[i // 8, i % 8, 1] = -1
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.WHITE):
            input[i // 8, i % 8, 2] = 1
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.BLACK):
            input[i // 8, i % 8, 2] = -1
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.WHITE):
            input[i // 8, i % 8, 3] = 1
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.BLACK):
            input[i // 8, i % 8, 3] = -1
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.WHITE):
            input[i // 8, i % 8, 4] = 1
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.BLACK):
            input[i // 8, i % 8, 4] = -1
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.WHITE):
            input[i // 8, i % 8, 5] = 1
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.BLACK):
            input[i // 8, i % 8, 5] = -1
        if not board.turn:
            input[i // 8, i % 8, 6] = -1
        else:
            input[i // 8, i % 8, 6] = 1

    return input


def nn_heuristic(fen, options, model):
    board = chess.Board(fen)

    # special eval conditions
    if board.is_game_over():
        if board.is_checkmate():
            return -25500
        else:
            return 0

    if options.fiftyMoveRule and int(fen.split(' ')[4]) >= 100:
        return 0

    # normal eval conditions
    else:
        eval = 0
        map = board.piece_map()

        # tablebase probing
        if len(map) <= options.syzygyProbeLimit and options.syzygyPath != '<empty>':
            with chess.syzygy.open_tablebase(
                    options.syzygyPath, load_wdl=True, max_fds=128) as tablebase:
                wdl = tablebase.get_wdl(board)
                if wdl is not None:
                    if options.fiftyMoveRule and wdl == -2:
                        eval = -12800
                    elif options.fiftyMoveRule and wdl == 2:
                        eval = 12800
                    elif not options.fiftyMoveRule and wdl == 1:
                        eval = 12800
                    elif not options.fiftyMoveRule and wdl == -1:
                        eval = -12800
                    else:
                        return 0
            tablebase.close()

        tab_eval = eval
        # create data to pass to net
        if '3-100k' in options.modelFile:
            data = np.array([fen_to_input(fen)])
            eval = (model.predict_classes(data)[0] - 3) * 100 + randrange(-50, 51, 1)
            return int(eval) + tab_eval
        elif options.network == "Classification":
            data = np.array([fen_to_input(fen)])
            eval = (model.predict_classes(data)[0] - 3) * 100 + randrange(-50, 51, 1)
            if board.turn:
                return int(eval) + tab_eval
            else:
                return -int(eval) + tab_eval
        elif 'model4_50k_wrong' in options.modelFile:
            data = np.array([fen_to_pieces_input(fen)])
            eval = model.predict(data, verbose=0)
            if board.turn:
                return int(round(eval[0][0] * 2000)) + tab_eval
            else:
                return -int(round(eval[0][0] * 2000)) + tab_eval
        elif '100k' in options.modelFile:
            data = np.array([fen_to_input(fen)])
            eval = model.predict(data, verbose=0)
            return int(round(eval[0][0] * 2000)) + tab_eval
        else:
            data = np.array([fen_to_input(fen)])
            eval = model.predict(data, verbose=0)
            if board.turn:
                return int(round(eval[0][0] * 2000)) + tab_eval
            else:
                return -int(round(eval[0][0] * 2000)) + tab_eval


def random_heuristic():
    return int(uniform(0, 2000))
