import chess
import chess.syzygy
from keras.models import load_model
import numpy as np
import time

def fen_to_input(fen):
    board = chess.Board(fen)
    inp = np.zeros(69)
    i = 0

    for i in range(0,64):
        if board.piece_at(i) == chess.Piece(chess.PAWN, chess.WHITE):
            inp[i] = 0.45
        elif board.piece_at(i) == chess.Piece(chess.PAWN, chess.BLACK):
            inp[i] = -0.45
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.WHITE):
            inp[i] = 0.55
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.BLACK):
            inp[i] = -0.55
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.WHITE):
            inp[i] = 0.65
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.BLACK):
            inp[i] = -0.65
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.WHITE):
            inp[i] = 0.75
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.BLACK):
            inp[i] = -0.75
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.WHITE):
            inp[i] = 0.85
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.BLACK):
            inp[i] = -0.85
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.WHITE):
            inp[i] = 0.95
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.BLACK):
            inp[i] = -0.95
        else:
            inp[i] = 0.1
        i += 1
    
    # special conditions
    if board.turn:
        inp[68] = 1
    if board.has_kingside_castling_rights(chess.WHITE):
        inp[64] = 1
    if board.has_queenside_castling_rights(chess.WHITE):
        inp[65] = 1
    if board.has_kingside_castling_rights(chess.BLACK):
        inp[66] = 1
    if board.has_queenside_castling_rights(chess.BLACK):
        inp[67] = 1
    
    return np.array(inp)

def fen_to_plane_input(fen):
    board = chess.Board(fen)
    input = np.zeros((8,8,3), dtype=int)

    for i in range(0,64):
        if board.piece_at(i) == chess.Piece(chess.PAWN, chess.WHITE):
            input[i//8,i%8,0] = 1
        elif board.piece_at(i) == chess.Piece(chess.PAWN, chess.BLACK):
            input[i//8,i%8,1] = 1
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.WHITE):
            input[i//8,i%8,0] = 2
        elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.BLACK):
            input[i//8,i%8,1] = 2
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.WHITE):
            input[i//8,i%8,0] = 3
        elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.BLACK):
            input[i//8,i%8,1] = 3
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.WHITE):
            input[i//8,i%8,0] = 4
        elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.BLACK):
            input[i//8,i%8,1] = 4
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.WHITE):
            input[i//8,i%8,0] = 5
        elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.BLACK):
            input[i//8,i%8,1] = 5
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.WHITE):
            input[i//8,i%8,0] = 6
        elif board.piece_at(i) == chess.Piece(chess.KING, chess.BLACK):
            input[i//8,i%8,1] = 6
        if board.turn:
            input[i//8,i%8,2] = 1
    
    return input

def p_to_cp(p):
    if p != 1:
        return 400*np.log10(p/(1-p))
    else:
        return 25500

def nn_heuristic(node, options, model):
    # special eval conditions
    if node.board.is_game_over():
        if node.board.is_checkmate() and node.board.turn:
            node.eval = -25500
            return
        elif node.board.is_checkmate() and (not node.board.turn):
            node.eval = 25500
            return
        elif node.board.is_stalemate():
            node.eval = 0
            return
    elif node.board.is_insufficient_material():
            node.eval = 0
            return
    elif node.board.can_claim_threefold_repetition():
            node.eval = 0
            return
    elif node.board.can_claim_fifty_moves() and options.fiftyMoveRule:
            node.eval = 0
            return
    
    # normal eval conditions
    else:
        eval = 0
        map = node.board.piece_map()

        # tablebase probing
        if len(map) <= options.syzygyProbeLimit and options.syzygyPath != '<empty>':
            with chess.syzygy.open_tablebase(options.syzygyPath, load_wdl=True, max_fds=128) as tablebase:
                wdl = tablebase.get_wdl(node.board)
                #dtz = tablebase.get_dtz(node.board)
                if wdl != None:
                    node.tablebasePosition = True
                    if options.fiftyMoveRule and wdl < -1:
                        if node.board.turn:
                            node.eval = -25500
                        else:
                            node.eval = 25500
                        return
                    elif options.fiftyMoveRule and wdl > 1:
                        if node.board.turn:
                            node.eval = 25500
                        else:
                            node.eval = -25500
                        return
                    elif not options.fiftyMoveRule and wdl > 0:
                        if node.board.turn:
                            node.eval = 25500
                        else:
                            node.eval = -25500
                        return
                    elif not options.fiftyMoveRule and wdl < -0:
                        if node.board.turn:
                            node.eval = -25500
                        else:
                            node.eval = 25500
                        return
                    else:
                        node.eval = 0
                        return
            tablebase.close()

        # create data to pass to net
        if options.nn_input_type == "planes":
            data = np.array([fen_to_plane_input(node.board.fen())])
        else:
            data = np.array([fen_to_input(node.board.fen())])
        eval = p_to_cp(model.predict(data))
        node.eval = round(eval[0][0])