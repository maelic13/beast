from chess import (
    BB_CENTER,
    BB_FILES,
    BISHOP,
    BLACK,
    KING,
    KNIGHT,
    PAWN,
    QUEEN,
    ROOK,
    WHITE,
    Board,
    square_file,
    square_mirror,
    square_rank,
)

from .infra import Heuristic, PieceValues


class ClassicalHeuristic(Heuristic):
    BISHOP_PAIR_BONUS = 35
    CONNECTED_PAWN_BONUS = 8
    DOUBLED_PAWN_PENALTY = 14
    ISOLATED_PAWN_PENALTY = 16
    PASSED_PAWN_BONUS = (0, 5, 10, 20, 36, 60, 95, 0)
    ROOK_OPEN_FILE_BONUS = 24
    ROOK_SEMI_OPEN_FILE_BONUS = 12
    ROOK_ON_SEVENTH_BONUS = 18
    TEMPO_BONUS = 12

    PAWN_MG = (
        0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, -20, -20, 10, 10, 5,
        5, -5, -10, 0, 0, -10, -5, 5,
        0, 0, 0, 25, 25, 0, 0, 0,
        5, 5, 10, 30, 30, 10, 5, 5,
        10, 10, 20, 35, 35, 20, 10, 10,
        50, 50, 50, 50, 50, 50, 50, 50,
        0, 0, 0, 0, 0, 0, 0, 0,
    )
    PAWN_EG = (
        0, 0, 0, 0, 0, 0, 0, 0,
        10, 10, 10, -10, -10, 10, 10, 10,
        10, 5, 5, 15, 15, 5, 5, 10,
        15, 15, 20, 30, 30, 20, 15, 15,
        20, 20, 30, 40, 40, 30, 20, 20,
        30, 30, 40, 55, 55, 40, 30, 30,
        60, 60, 60, 60, 60, 60, 60, 60,
        0, 0, 0, 0, 0, 0, 0, 0,
    )
    KNIGHT_MG = (
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50,
    )
    KNIGHT_EG = (
        -40, -25, -20, -20, -20, -20, -25, -40,
        -25, -10, 0, 5, 5, 0, -10, -25,
        -20, 5, 10, 15, 15, 10, 5, -20,
        -20, 10, 15, 20, 20, 15, 10, -20,
        -20, 10, 15, 20, 20, 15, 10, -20,
        -20, 5, 10, 15, 15, 10, 5, -20,
        -25, -10, 0, 5, 5, 0, -10, -25,
        -40, -25, -20, -20, -20, -20, -25, -40,
    )
    BISHOP_MG = (
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -20, -10, -10, -10, -10, -10, -10, -20,
    )
    BISHOP_EG = (
        -15, -10, -8, -8, -8, -8, -10, -15,
        -10, 0, 2, 5, 5, 2, 0, -10,
        -8, 2, 8, 10, 10, 8, 2, -8,
        -8, 5, 10, 12, 12, 10, 5, -8,
        -8, 5, 10, 12, 12, 10, 5, -8,
        -8, 2, 8, 10, 10, 8, 2, -8,
        -10, 0, 2, 5, 5, 2, 0, -10,
        -15, -10, -8, -8, -8, -8, -10, -15,
    )
    ROOK_MG = (
        0, 0, 5, 10, 10, 5, 0, 0,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        15, 20, 20, 20, 20, 20, 20, 15,
        0, 0, 5, 10, 10, 5, 0, 0,
    )
    ROOK_EG = (
        0, 5, 10, 12, 12, 10, 5, 0,
        0, 5, 10, 12, 12, 10, 5, 0,
        0, 5, 10, 12, 12, 10, 5, 0,
        0, 5, 10, 12, 12, 10, 5, 0,
        0, 5, 10, 12, 12, 10, 5, 0,
        0, 5, 10, 12, 12, 10, 5, 0,
        5, 10, 12, 15, 15, 12, 10, 5,
        0, 5, 10, 12, 12, 10, 5, 0,
    )
    QUEEN_MG = (
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20,
    )
    QUEEN_EG = (
        -10, -5, -5, 0, 0, -5, -5, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        -5, 5, 8, 10, 10, 8, 5, -5,
        0, 5, 10, 12, 12, 10, 5, 0,
        0, 5, 10, 12, 12, 10, 5, 0,
        -5, 5, 8, 10, 10, 8, 5, -5,
        -5, 0, 5, 5, 5, 5, 0, -5,
        -10, -5, -5, 0, 0, -5, -5, -10,
    )
    KING_MG = (
        20, 30, 10, 0, 0, 10, 30, 20,
        20, 20, 0, 0, 0, 0, 20, 20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
    )
    KING_EG = (
        -50, -30, -20, -20, -20, -20, -30, -50,
        -30, -10, 0, 0, 0, 0, -10, -30,
        -20, 0, 10, 15, 15, 10, 0, -20,
        -20, 0, 15, 20, 20, 15, 0, -20,
        -20, 0, 15, 20, 20, 15, 0, -20,
        -20, 0, 10, 15, 15, 10, 0, -20,
        -30, -10, 0, 0, 0, 0, -10, -30,
        -50, -30, -20, -20, -20, -20, -30, -50,
    )

    def _evaluate_internal(self, board: Board) -> float:
        middle_game_score = 0
        end_game_score = 0

        middle_game_score += self.TEMPO_BONUS if board.turn == WHITE else -self.TEMPO_BONUS

        middle_game_score += self._evaluate_side(board, WHITE)
        middle_game_score -= self._evaluate_side(board, BLACK)

        end_game_score += self._evaluate_side(board, WHITE, endgame=True)
        end_game_score -= self._evaluate_side(board, BLACK, endgame=True)

        phase = self._phase(board)
        evaluation = (middle_game_score * phase + end_game_score * (24 - phase)) / 24
        return int(evaluation if board.turn == WHITE else -evaluation)

    def _evaluate_side(self, board: Board, color: bool, *, endgame: bool = False) -> int:
        pawns = board.pieces(PAWN, color)
        knights = board.pieces(KNIGHT, color)
        bishops = board.pieces(BISHOP, color)
        rooks = board.pieces(ROOK, color)
        queens = board.pieces(QUEEN, color)
        king = board.king(color)

        if king is None:
            return 0

        score = 0
        score += len(pawns) * PieceValues.PAWN_VALUE
        score += len(knights) * PieceValues.KNIGHT_VALUE
        score += len(bishops) * PieceValues.BISHOP_VALUE
        score += len(rooks) * PieceValues.ROOK_VALUE
        score += len(queens) * PieceValues.QUEEN_VALUE

        for square in pawns:
            score += self._psqt(PAWN, square, color, endgame=endgame)
            score += self._pawn_structure_bonus(board, square, color)

        for square in knights:
            score += self._psqt(KNIGHT, square, color, endgame=endgame)

        for square in bishops:
            score += self._psqt(BISHOP, square, color, endgame=endgame)

        for square in rooks:
            score += self._psqt(ROOK, square, color, endgame=endgame)
            score += self._rook_file_bonus(board, square, color)

        for square in queens:
            score += self._psqt(QUEEN, square, color, endgame=endgame)

        score += self._psqt(KING, king, color, endgame=endgame)
        score += self._mobility(board, color, endgame=endgame)
        score += self._bishop_pair_bonus(bishops)
        score += self._king_safety(board, color, endgame=endgame)

        if endgame:
            score += self._endgame_king_pressure(board, color)

        return score

    def _mobility(self, board: Board, color: bool, *, endgame: bool) -> int:
        own_pawns = board.pieces(PAWN, color)
        own_king = board.king(color)
        if own_king is None:
            return 0

        knight_mobility = 0
        for square in board.pieces(KNIGHT, color):
            knight_mobility += len(board.attacks(square) & ~own_pawns)

        bishop_mobility = 0
        for square in board.pieces(BISHOP, color):
            bishop_mobility += len(board.attacks(square))

        rook_mobility = 0
        for square in board.pieces(ROOK, color):
            rook_mobility += len(board.attacks(square))

        queen_mobility = 0
        for square in board.pieces(QUEEN, color):
            queen_mobility += len(board.attacks(square))

        king_zone = len(board.attacks(own_king) & BB_CENTER)
        if endgame:
            return (
                knight_mobility * 3
                + bishop_mobility * 3
                + rook_mobility * 2
                + queen_mobility * 1
                + king_zone * 3
            )

        return (
            knight_mobility * 4
            + bishop_mobility * 4
            + rook_mobility * 2
            + queen_mobility
        )

    def _pawn_structure_bonus(self, board: Board, square: int, color: bool) -> int:
        file_index = square_file(square)
        rank_index = square_rank(square) if color == WHITE else 7 - square_rank(square)
        own_pawns = board.pieces(PAWN, color)
        enemy_pawns = board.pieces(PAWN, not color)
        file_mask = BB_FILES[file_index]
        adjacent_mask = 0
        if file_index > 0:
            adjacent_mask |= BB_FILES[file_index - 1]
        if file_index < 7:
            adjacent_mask |= BB_FILES[file_index + 1]

        score = 0
        if len(own_pawns & file_mask) > 1:
            score -= self.DOUBLED_PAWN_PENALTY
        if not own_pawns & adjacent_mask:
            score -= self.ISOLATED_PAWN_PENALTY
        if own_pawns & board.attacks(square):
            score += self.CONNECTED_PAWN_BONUS
        if self._is_passed_pawn(square, color, enemy_pawns):
            score += self.PASSED_PAWN_BONUS[rank_index]
        return score

    def _is_passed_pawn(self, square: int, color: bool, enemy_pawns: int) -> bool:
        file_index = square_file(square)
        rank_index = square_rank(square)
        for enemy_square in enemy_pawns:
            enemy_file = square_file(enemy_square)
            if abs(enemy_file - file_index) > 1:
                continue
            enemy_rank = square_rank(enemy_square)
            if color == WHITE and enemy_rank > rank_index:
                return False
            if color == BLACK and enemy_rank < rank_index:
                return False
        return True

    def _rook_file_bonus(self, board: Board, square: int, color: bool) -> int:
        file_mask = BB_FILES[square_file(square)]
        own_pawns = board.pieces(PAWN, color)
        enemy_pawns = board.pieces(PAWN, not color)

        score = 0
        if not own_pawns & file_mask:
            score += self.ROOK_SEMI_OPEN_FILE_BONUS
            if not enemy_pawns & file_mask:
                score += self.ROOK_OPEN_FILE_BONUS - self.ROOK_SEMI_OPEN_FILE_BONUS

        target_rank = 6 if color == WHITE else 1
        if square_rank(square) == target_rank:
            score += self.ROOK_ON_SEVENTH_BONUS

        return score

    def _bishop_pair_bonus(self, bishops: int) -> int:
        return self.BISHOP_PAIR_BONUS if len(bishops) >= 2 else 0

    def _king_safety(self, board: Board, color: bool, *, endgame: bool) -> int:
        if endgame:
            return 0

        king = board.king(color)
        if king is None:
            return 0

        file_index = square_file(king)
        rank_index = square_rank(king)
        shield_rank = rank_index + 1 if color == WHITE else rank_index - 1
        shield = 0
        if 0 <= shield_rank <= 7:
            for next_file in range(max(0, file_index - 1), min(7, file_index + 1) + 1):
                square = shield_rank * 8 + next_file
                if board.piece_type_at(square) == PAWN and board.color_at(square) == color:
                    shield += 12

        attackers = len(board.attackers(not color, king))
        return shield - attackers * 18

    def _endgame_king_pressure(self, board: Board, color: bool) -> int:
        own_king = board.king(color)
        enemy_king = board.king(not color)
        if own_king is None or enemy_king is None:
            return 0

        distance = abs(square_file(own_king) - square_file(enemy_king)) + abs(
            square_rank(own_king) - square_rank(enemy_king)
        )
        enemy_center_distance = abs(square_file(enemy_king) - 3.5) + abs(square_rank(enemy_king) - 3.5)
        return int((14 - distance) * 3 + enemy_center_distance * 4)

    @staticmethod
    def _phase(board: Board) -> int:
        phase = 0
        phase += len(board.pieces(QUEEN, WHITE)) * 4
        phase += len(board.pieces(QUEEN, BLACK)) * 4
        phase += len(board.pieces(ROOK, WHITE)) * 2
        phase += len(board.pieces(ROOK, BLACK)) * 2
        phase += len(board.pieces(BISHOP, WHITE))
        phase += len(board.pieces(BISHOP, BLACK))
        phase += len(board.pieces(KNIGHT, WHITE))
        phase += len(board.pieces(KNIGHT, BLACK))
        return max(0, min(24, phase))

    def _psqt(self, piece_type: int, square: int, color: bool, *, endgame: bool) -> int:
        index = square if color == WHITE else square_mirror(square)
        return self._psqt_table(piece_type, endgame)[index]

    def _psqt_table(self, piece_type: int, endgame: bool) -> tuple[int, ...]:
        if piece_type == PAWN:
            return self.PAWN_EG if endgame else self.PAWN_MG
        if piece_type == KNIGHT:
            return self.KNIGHT_EG if endgame else self.KNIGHT_MG
        if piece_type == BISHOP:
            return self.BISHOP_EG if endgame else self.BISHOP_MG
        if piece_type == ROOK:
            return self.ROOK_EG if endgame else self.ROOK_MG
        if piece_type == QUEEN:
            return self.QUEEN_EG if endgame else self.QUEEN_MG
        return self.KING_EG if endgame else self.KING_MG
