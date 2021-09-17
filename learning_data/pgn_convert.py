import chess
import numpy as np
import chess.pgn as pgn
import chess.engine
import time


def parse_pgn(number):
    games = open('./learning_data/games_50k.pgn', encoding="UTF-8-SIG")
    positions = []
    evaluations1 = []
    evaluations2 = []
    inp = []
    start_time = time.time()
    engine = chess.engine.SimpleEngine.popen_uci(
        "C:/Users/maelic/Documents/Chessbase/Engines/stockfish_x64_bmi2.exe")

    i = 0
    while True:
        i += 1
        game = pgn.read_game(games)
        if game is None:
            break
        board = game.board()

        for move in game.mainline_moves():
            board.push(move)
            fen = board.fen()

            # check for doubles
            if fen in positions:
                continue

            # Evaluate by Stockfish
            info1 = engine.analyse(board, chess.engine.Limit(depth=10))
            info2 = engine.analyse(board, chess.engine.Limit(depth=5))
            evaluation1 = str(info1["score"])
            evaluation2 = str(info2["score"])

            # Correct and limit evaluation to +- 2000cp (20 pawns)
            if evaluation1.startswith("#+"):
                evaluation1 = 2000
            elif evaluation1.startswith("#-"):
                evaluation1 = -2000
            elif int(evaluation1) > 2000:
                evaluation1 = 2000
            elif int(evaluation1) < -2000:
                evaluation1 = -2000

            if evaluation2.startswith("#+"):
                evaluation2 = 2000
            elif evaluation2.startswith("#-"):
                evaluation2 = -2000
            elif int(evaluation2) > 2000:
                evaluation2 = 2000
            elif int(evaluation2) < -2000:
                evaluation2 = -2000

            # convert to integers
            evaluation1 = int(evaluation1)
            evaluation2 = int(evaluation2)

            evaluations1.append(evaluation1)
            evaluations2.append(evaluation2)
            positions.append(fen)
            inp.append(fen_to_input(fen))

        if i % 1000 == 0 or i % number == 0:
            speed = i / (time.time() - start_time)
            print('Finished', i, 'games out of', number)
            print('Time elapsed:', (time.time() - start) / 3600, 'hours')
            print('Speed:', speed * 60, 'games/min')
            print('Estimated time left:', 3 * ((number - i) / speed) / 3600, 'hours\n')

    inp = np.array(inp)
    engine.close()
    return inp, evaluations1, evaluations2


def eval_to_output(evaluations1, evaluations2):
    # Prepare output
    single_output_depth5 = []
    single_output_depth10 = []
    for i in range(0, len(evaluations1)):
        try:
            single_output_depth10.append(float(evaluations1[i]) / 2000)
            single_output_depth5.append(float(evaluations2[i]) / 2000)
        except:
            break
    single_output_depth5 = np.array(single_output_depth5)
    single_output_depth10 = np.array(single_output_depth10)

    class_output_depth5 = []
    class_output_depth10 = []
    for i in range(0, len(evaluations1)):
        try:
            class_output_depth10.append(eval_to_sparse_7_class(evaluations1[i]))
            class_output_depth5.append(eval_to_sparse_7_class(evaluations2[i]))
        except:
            break
    class_output_depth10 = np.array(class_output_depth10)
    class_output_depth5 = np.array(class_output_depth5)

    return class_output_depth5, class_output_depth10, single_output_depth5, single_output_depth10


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


def fen_to_just_pieces_input(fen):
    board = chess.Board(fen)
    input_planes = np.zeros((6, 8, 8), dtype=int)

    for i in range(0, 64):
        if board.turn:
            if board.piece_at(i) == chess.Piece(chess.PAWN, chess.WHITE):
                input_planes[0, i // 8, i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.PAWN, chess.BLACK):
                input_planes[0, i // 8, i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.WHITE):
                input_planes[1, i // 8, i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.BLACK):
                input_planes[1, i // 8, i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.WHITE):
                input_planes[2, i // 8, i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.BLACK):
                input_planes[2, i // 8, i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.WHITE):
                input_planes[3, i // 8, i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.BLACK):
                input_planes[3, i // 8, i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.WHITE):
                input_planes[4, i // 8, i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.BLACK):
                input_planes[4, i // 8, i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.KING, chess.WHITE):
                input_planes[5, i // 8, i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.KING, chess.BLACK):
                input_planes[5, i // 8, i % 8] = -1
        else:
            if board.piece_at(i) == chess.Piece(chess.PAWN, chess.WHITE):
                input_planes[0, 7 - i // 8, 7 - i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.PAWN, chess.BLACK):
                input_planes[0, 7 - i // 8, 7 - i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.WHITE):
                input_planes[1, 7 - i // 8, 7 - i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.KNIGHT, chess.BLACK):
                input_planes[1, 7 - i // 8, 7 - i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.WHITE):
                input_planes[2, 7 - i // 8, 7 - i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.BISHOP, chess.BLACK):
                input_planes[2, 7 - i // 8, 7 - i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.WHITE):
                input_planes[3, 7 - i // 8, 7 - i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.ROOK, chess.BLACK):
                input_planes[3, 7 - i // 8, 7 - i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.WHITE):
                input_planes[4, 7 - i // 8, 7 - i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.QUEEN, chess.BLACK):
                input_planes[4, 7 - i // 8, 7 - i % 8] = 1
            elif board.piece_at(i) == chess.Piece(chess.KING, chess.WHITE):
                input_planes[5, 7 - i // 8, 7 - i % 8] = -1
            elif board.piece_at(i) == chess.Piece(chess.KING, chess.BLACK):
                input_planes[5, 7 - i // 8, 7 - i % 8] = 1

    return input_planes


def eval_to_sparse_7_class(evaluation):
    # create data for evaluation into 7 groups
    # +-100     -> 3 -> draw
    # 100-300   -> 2,4
    # 300-600   -> 1,5
    # 600+      -> 0,6 -> won

    output = 0
    # draw
    if 100 >= evaluation >= -100:
        output = 3
    # better for white
    elif 100 < evaluation <= 300:
        output = 4
    elif 300 < evaluation <= 600:
        output = 5
    elif evaluation > 600:
        output = 6
    # better for black
    elif -100 > evaluation >= -300:
        output = 2
    elif -300 > evaluation >= -600:
        output = 1
    elif evaluation < -600:
        output = 0
    return output


if __name__ == '__main__':
    start = time.time()
    # Load PGN and parse it into positions
    print('Parsing PGN\n')
    number_of_games = 50000
    inputs, evals1, evals2 = parse_pgn(number_of_games)

    # Evaluate positions
    print('Evaluating positions')
    class_output_d5, class_output_d10, single_output_d5, single_output_d10 = eval_to_output(
        evals1, evals2)

    # Save as .npy files
    print('Saving .npy files')
    np.save('C:/Users/maelic/Documents/VUT/DP/learning_data/data/input', inputs)
    np.save('C:/Users/maelic/Documents/VUT/DP/learning_data/data/class_output_d5', class_output_d5)
    np.save('C:/Users/maelic/Documents/VUT/DP/learning_data/data/class_output_d10',
            class_output_d10)
    np.save('C:/Users/maelic/Documents/VUT/DP/learning_data/data/single_output_d5',
            single_output_d5)
    np.save('C:/Users/maelic/Documents/VUT/DP/learning_data/data/single_output_d10',
            single_output_d10)
    end = time.time()
    print('Total time:', (end - start) / 3600, 'hours')
