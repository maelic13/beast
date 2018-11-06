import chess

bo = chess.Board('5Rnk/6pp/3q1b2/3p1P2/B1pP2Q1/P1p5/P6P/4R2K b - - 0 36')

print(bo.is_capture(chess.Move.from_uci('d6f7')))