import chess
import math

def heuristic(node, fiftyMoveRule):
    if node.getBoard().is_game_over():
        if node.getBoard().is_checkmate() and node.getBoard().turn:
            node.setEval(-25500)
            return
        elif node.getBoard().is_checkmate() and (not node.getBoard().turn):
            node.setEval(25500)
            return
        elif node.getBoard().is_stalemate():
            node.setEval(0)
            return
    elif node.getBoard().is_insufficient_material():
            node.setEval(0)
            return
    elif node.getBoard().can_claim_threefold_repetition():
            node.setEval(0)
            return
    elif node.getBoard().can_claim_fifty_moves() and fiftyMoveRule:
            node.setEval(0)
            return
    else:
        evalTable = [100, 295, 315, 500, 900]
        eval = 0
        for i in range(0, 64):
            piece = node.getBoard().piece_at(i)
            pieceValue = 0
            if piece == chess.Piece(chess.PAWN, chess.WHITE):
                pieceValue = evalTable[0]
            elif piece == chess.Piece(chess.PAWN, chess.BLACK):
                pieceValue = -evalTable[0]
            elif piece == chess.Piece(chess.KNIGHT, chess.WHITE):
                pieceValue = evalTable[1]
            elif piece == chess.Piece(chess.KNIGHT, chess.BLACK):
                pieceValue = -evalTable[1]
            elif piece == chess.Piece(chess.BISHOP, chess.WHITE):
                pieceValue = evalTable[2]
            elif piece == chess.Piece(chess.BISHOP, chess.BLACK):
                pieceValue = -evalTable[2]
            elif piece == chess.Piece(chess.ROOK, chess.WHITE):
                pieceValue = evalTable[3]
            elif piece == chess.Piece(chess.ROOK, chess.BLACK):
                pieceValue = -evalTable[3]
            elif piece == chess.Piece(chess.QUEEN, chess.WHITE):
                pieceValue = evalTable[4]
            elif piece == chess.Piece(chess.QUEEN, chess.BLACK):
                pieceValue = -evalTable[4]
            
            # add square and other conditions
            if i==27 or i==28 or i==35 or i==36:
                pieceValue = pieceValue * 1.05
            
            if node.getBoard().turn:
                opponentKing = node.getBoard().king(chess.BLACK)
                distance = math.sqrt((opponentKing%8 - i%8)**2 + (int(opponentKing/8) - int(i/8))**2)
                pieceValue -= distance*0.01
            else:
                opponentKing = node.getBoard().king(chess.WHITE)
                distance = math.sqrt((opponentKing%8 - i%8)**2 + (int(opponentKing/8) - int(i/8))**2)
                pieceValue += distance*0.01
            
            eval += pieceValue
    node.setEval(eval)