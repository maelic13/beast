import chess
import chess.syzygy

# VARIABLES
# Parameter weights for bonus eval
pawnRankW = 5
pawnFileW = 5
pawnCenterW = 5
pawnDistanceW = 5

knightCenterW = 8
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
def heuristic(node, options):
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
        evalTable = [100, 285, 315, 500, 900]
        eval = 0
        map = node.board.piece_map()

        # tablebase probing
        if len(map) <= options.syzygyProbeLimit and options.syzygyPath != '<empty>':
            with chess.syzygy.open_tablebases(options.syzygyPath, load_wdl=True, max_fds=128) as tablebase:
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
            if node.board.piece_at(each) == chess.Piece(chess.PAWN, chess.WHITE):
                wPawns.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.PAWN, chess.BLACK):
                bPawns.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.KNIGHT, chess.WHITE):
                wKnights.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.KNIGHT, chess.BLACK):
                bKnights.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.BISHOP, chess.WHITE):
                wBishops.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.BISHOP, chess.BLACK):
                bBishops.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.ROOK, chess.WHITE):
                wRooks.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.ROOK, chess.BLACK):
                bRooks.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.QUEEN, chess.WHITE):
                wQueens.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.QUEEN, chess.BLACK):
                bQueens.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.KING, chess.WHITE):
                wKing.append(each)
            if node.board.piece_at(each) == chess.Piece(chess.KING, chess.BLACK):
                bKing.append(each)

        # Initial eval - adding value of pieceson board
        eval =  (
            len(wPawns)*evalTable[0]    -   len(bPawns)*evalTable[0]    +
            len(wKnights)*evalTable[1]  -   len(bKnights)*evalTable[1]  +
            len(wBishops)*evalTable[2]  -   len(bBishops)*evalTable[2]  +
            len(wRooks)*evalTable[3]    -   len(bRooks)*evalTable[3]    +
            len(wQueens)*evalTable[4]   -   len(bQueens)*evalTable[4]
            )
            
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
        wkingBonus = kingBonus(wKing, bKing, bQueens==[])
        bkingBonus = kingBonus(bKing, wKing, wQueens==[])

        # Add bonuses to eval
        eval += (
            wpBonus - bpBonus +
            wkBonus - bkBonus +
            wbBonus - bbBonus +
            wrBonus - brBonus +
            wqBonus - bqBonus +
            wkingBonus - bkingBonus
            )
        # Assign eval to node
        node.eval = eval

def pawnBonus(pawns, king, color):
    pBonus = 0
    for each in pawns:
        # rank bonus -> the further the pawn, the more of a bonus
        if color:
            pBonus += (int(each/8) - 1) * pawnRankW
        else:
            pBonus += (6 - int(each/8)) * pawnRankW
        # file decrement -> central files take nothing, the closer to rim, the less pawn's value
        if each%8 < 3:
            pBonus -= (3 - each%8) * pawnFileW
        elif each%8 > 4:
            pBonus -= (each%8 - 4) * pawnFileW
        else:
            pass

        # occupying center bonus
        if int(each/8) in range(3,5) and each%8 in range(3,5):
            pBonus += pawnCenterW
        if int(each/8) in range(2,6) and each%8 in range(2,6):
            pBonus += pawnCenterW
        if int(each/8) in range(1,7) and each%8 in range(1,7):
            pBonus += pawnCenterW

        # distance from king bonus
        distance = abs(int(each/8) - int(king[0]/8)) + abs(each%8 - king[0]%8)
        pBonus += 14/distance * pawnDistanceW - pawnDistanceW

    return pBonus

def knightBonus(knights, king, color):
    kBonus = 0
    for each in knights:
        # occupying center bonus
        if int(each/8) in range(3,5) and each%8 in range(3,5):
            kBonus += knightCenterW
        if int(each/8) in range(2,6) and each%8 in range(2,6):
            kBonus += knightCenterW
        if int(each/8) in range(1,7) and each%8 in range(1,7):
            kBonus += knightCenterW

        # distance from king bonus
        distance = abs(int(each/8) - int(king[0]/8)) + abs(each%8 - king[0]%8)
        kBonus += 14/distance * knightDistanceW - knightDistanceW
    return kBonus

def bishopBonus(bishops, king, color):
    bBonus = 0
    for each in bishops:
        # occupying center bonus
        if int(each/8) in range(3,5) and each%8 in range(3,5):
            bBonus += bishopCenterW
        if int(each/8) in range(2,6) and each%8 in range(2,6):
            bBonus += bishopCenterW
        if int(each/8) in range(1,7) and each%8 in range(1,7):
            bBonus += bishopCenterW

        # distance from king bonus
        distance = abs(int(each/8) - int(king[0]/8)) + abs(each%8 - king[0]%8)
        bBonus += 14/distance * bishopDistanceW - bishopDistanceW
    return bBonus

def rookBonus(rooks, king, color):
    rBonus = 0
    for each in rooks:
        # occupying center bonus
        if each%8 in range(3,5):
            rBonus += rookCenterW
        if each%8 in range(2,6):
            rBonus += rookCenterW
        if each%8 in range(1,7):
            rBonus += rookCenterW

        # distance from king bonus
        distance = abs(int(each/8) - int(king[0]/8)) + abs(each%8 - king[0]%8)
        rBonus += 14/distance * rookDistanceW - rookDistanceW
    return rBonus

def queenBonus(queens, king, color):
    qBonus = 0
    for each in queens:
        # occupying center bonus
        if int(each/8) in range(3,5) and each%8 in range(3,5):
            qBonus += queenCenterW
        if int(each/8) in range(2,6) and each%8 in range(2,6):
            qBonus += queenCenterW
        if int(each/8) in range(1,7) and each%8 in range(1,7):
            qBonus += queenCenterW

        # distance from king bonus
        distance = abs(int(each/8) - int(king[0]/8)) + abs(each%8 - king[0]%8)
        qBonus += 14/distance * queenDistanceW - queenDistanceW
    return qBonus

def kingBonus(king, oponentKing, noQueen):
    kingBonus = 0
    if noQueen:
        kingCenterW = kingCenterWvalue
    else:
        kingCenterW = -kingCenterWvalue

    for each in king:
        # occupying center bonus
        if int(each/8) in range(3,5) and each%8 in range(3,5):
            kingBonus += kingCenterW
        if int(each/8) in range(2,6) and each%8 in range(2,6):
            kingBonus += kingCenterW
        if int(each/8) in range(1,7) and each%8 in range(1,7):
            kingBonus += kingCenterW

        # distance from king bonus
        distance = abs(int(each/8) - int(oponentKing[0]/8)) + abs(each%8 - oponentKing[0]%8)
        kingBonus += 14/distance * kingDistanceW - kingDistanceW
    return kingBonus

def main():
    pass

if __name__ == '__main__':
    main()