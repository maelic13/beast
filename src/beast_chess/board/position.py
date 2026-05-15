from __future__ import annotations

# ruff: noqa: SLF001
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

from .attacks import (
    BISHOP_RAYS,
    KING_ATTACKS,
    KNIGHT_ATTACKS,
    PAWN_ATTACKS,
    ROOK_RAYS,
    bishop_attacks,
    iter_bits,
    popcount,
    queen_attacks,
    rook_attacks,
)
from .constants import (
    A1,
    A8,
    ALL_CASTLING_RIGHTS,
    B1,
    B8,
    BB_ALL,
    BB_FILE_A,
    BB_FILE_H,
    BB_RANK_1,
    BB_RANK_2,
    BB_RANK_3,
    BB_RANK_6,
    BB_RANK_7,
    BB_RANK_8,
    BB_SQUARES,
    BISHOP,
    BLACK,
    BLACK_KINGSIDE,
    BLACK_QUEENSIDE,
    C1,
    C8,
    CASTLING_RIGHTS_MASKS,
    D1,
    D8,
    E1,
    E8,
    F1,
    F8,
    G1,
    G8,
    H1,
    H8,
    KING,
    KNIGHT,
    NO_PIECE,
    NO_SQUARE,
    PAWN,
    PROMOTION_PIECES,
    QUEEN,
    ROOK,
    STARTING_FEN,
    SYMBOL_TO_PIECE,
    WHITE,
    WHITE_KINGSIDE,
    WHITE_QUEENSIDE,
    file_of,
    opposite,
    parse_square,
    piece_code,
    piece_color,
    piece_symbol,
    piece_type,
    square_name,
)
from .move import (
    CAPTURE,
    CASTLING,
    DOUBLE_PAWN_PUSH,
    EN_PASSANT,
    NULL_MOVE,
    PROMOTION,
    Move,
    encode_move,
    from_square,
    is_en_passant,
    parse_uci_squares,
    same_move,
    to_square,
    uci,
)
from .move import (
    is_capture as move_is_capture,
)
from .zobrist import CASTLING_KEYS, EN_PASSANT_FILE_KEYS, PIECE_KEYS, SIDE_TO_MOVE_KEY


@dataclass(slots=True)
class _UndoState:
    move: Move
    moved_piece: int
    captured_piece: int
    captured_square: int
    castling_rights: int
    ep_square: int
    halfmove_clock: int
    fullmove_number: int
    zobrist_key: int


class Board:  # noqa: PLR0904
    __slots__ = (
        "_castling_rights",
        "_ep_square",
        "_fullmove_number",
        "_halfmove_clock",
        "_history",
        "_key_history",
        "_king_squares",
        "_occupancy_by_color",
        "_occupied",
        "_piece_bitboards",
        "_side_to_move",
        "_squares",
        "_zobrist_key",
    )

    def __init__(self, fen: str = STARTING_FEN) -> None:
        self._piece_bitboards = [0] * 13
        self._occupancy_by_color = [0, 0]
        self._occupied = 0
        self._squares = [NO_PIECE] * 64
        self._king_squares = [NO_SQUARE, NO_SQUARE]
        self._side_to_move = WHITE
        self._castling_rights = 0
        self._ep_square = NO_SQUARE
        self._halfmove_clock = 0
        self._fullmove_number = 1
        self._zobrist_key = 0
        self._history: list[_UndoState] = []
        self._key_history: list[int] = []
        self.set_fen(fen)

    @classmethod
    def empty(cls) -> Board:
        board = cls.__new__(cls)
        board._piece_bitboards = [0] * 13
        board._occupancy_by_color = [0, 0]
        board._occupied = 0
        board._squares = [NO_PIECE] * 64
        board._king_squares = [NO_SQUARE, NO_SQUARE]
        board._side_to_move = WHITE
        board._castling_rights = 0
        board._ep_square = NO_SQUARE
        board._halfmove_clock = 0
        board._fullmove_number = 1
        board._zobrist_key = 0
        board._history = []
        board._key_history = []
        return board

    @classmethod
    def from_fen(cls, fen: str) -> Board:
        return cls(fen)

    @classmethod
    def startpos(cls) -> Board:
        return cls(STARTING_FEN)

    def copy(self, *, stack: bool = False) -> Board:
        board = self.empty()
        board._piece_bitboards = self._piece_bitboards.copy()
        board._occupancy_by_color = self._occupancy_by_color.copy()
        board._occupied = self._occupied
        board._squares = self._squares.copy()
        board._king_squares = self._king_squares.copy()
        board._side_to_move = self._side_to_move
        board._castling_rights = self._castling_rights
        board._ep_square = self._ep_square
        board._halfmove_clock = self._halfmove_clock
        board._fullmove_number = self._fullmove_number
        board._zobrist_key = self._zobrist_key
        board._history = self._history.copy() if stack else []
        board._key_history = self._key_history.copy() if stack else [self._zobrist_key]
        return board

    @property
    def side_to_move(self) -> int:
        return self._side_to_move

    @property
    def turn(self) -> bool:
        return self._side_to_move == WHITE

    @property
    def castling_rights(self) -> int:
        return self._castling_rights

    @property
    def ep_square(self) -> int:
        return self._ep_square

    @property
    def halfmove_clock(self) -> int:
        return self._halfmove_clock

    @property
    def fullmove_number(self) -> int:
        return self._fullmove_number

    @property
    def zobrist_key(self) -> int:
        return self._zobrist_key

    @property
    def occupied(self) -> int:
        return self._occupied

    @property
    def occupied_co(self) -> tuple[int, int]:
        return self._occupancy_by_color[WHITE], self._occupancy_by_color[BLACK]

    @property
    def legal_moves(self) -> tuple[Move, ...]:
        return tuple(self.generate_legal_moves())

    @property
    def pseudo_legal_moves(self) -> tuple[Move, ...]:
        return tuple(self.generate_pseudo_legal_moves())

    @property
    def move_stack(self) -> tuple[Move, ...]:
        return tuple(state[0] for state in self._history)

    def set_fen(self, fen: str) -> None:
        if fen == "startpos":
            fen = STARTING_FEN
        parts = fen.split()
        if len(parts) < 4:
            msg = f"FEN requires at least 4 fields: {fen}"
            raise ValueError(msg)

        self._piece_bitboards = [0] * 13
        self._occupancy_by_color = [0, 0]
        self._occupied = 0
        self._squares = [NO_PIECE] * 64
        self._king_squares = [NO_SQUARE, NO_SQUARE]
        self._side_to_move = WHITE
        self._castling_rights = 0
        self._ep_square = NO_SQUARE
        self._halfmove_clock = int(parts[4]) if len(parts) > 4 else 0
        self._fullmove_number = int(parts[5]) if len(parts) > 5 else 1
        self._zobrist_key = 0
        self._history = []

        self._set_board_fen(parts[0])
        self._side_to_move = WHITE if parts[1] == "w" else BLACK
        self._castling_rights = self._parse_castling_rights(parts[2])
        self._ep_square = NO_SQUARE if parts[3] == "-" else parse_square(parts[3])
        self._zobrist_key ^= CASTLING_KEYS[self._castling_rights]
        if self._side_to_move == BLACK:
            self._zobrist_key ^= SIDE_TO_MOVE_KEY
        ep_hash_file = self._ep_hash_file(self._ep_square, self._side_to_move)
        if ep_hash_file != NO_SQUARE:
            self._zobrist_key ^= EN_PASSANT_FILE_KEYS[ep_hash_file]
        self._key_history = [self._zobrist_key]

    def _set_board_fen(self, board_fen: str) -> None:
        rows = board_fen.split("/")
        if len(rows) != 8:
            msg = f"Invalid FEN board field: {board_fen}"
            raise ValueError(msg)

        for fen_rank, row in enumerate(rows):
            rank = 7 - fen_rank
            file_index = 0
            for symbol in row:
                if symbol.isdigit():
                    file_index += int(symbol)
                    continue
                if symbol not in SYMBOL_TO_PIECE:
                    msg = f"Invalid piece symbol in FEN: {symbol}"
                    raise ValueError(msg)
                if file_index >= 8:
                    msg = f"Too many squares in FEN row: {row}"
                    raise ValueError(msg)
                self._put_piece(SYMBOL_TO_PIECE[symbol], rank * 8 + file_index)
                file_index += 1
            if file_index != 8:
                msg = f"FEN row does not contain 8 squares: {row}"
                raise ValueError(msg)

    @staticmethod
    def _parse_castling_rights(value: str) -> int:
        if value == "-":
            return 0
        rights = 0
        if "K" in value:
            rights |= WHITE_KINGSIDE
        if "Q" in value:
            rights |= WHITE_QUEENSIDE
        if "k" in value:
            rights |= BLACK_KINGSIDE
        if "q" in value:
            rights |= BLACK_QUEENSIDE
        return rights & ALL_CASTLING_RIGHTS

    def board_fen(self) -> str:
        rows: list[str] = []
        for rank in range(7, -1, -1):
            empty_count = 0
            row = []
            for file_index in range(8):
                piece = self._squares[rank * 8 + file_index]
                if piece == NO_PIECE:
                    empty_count += 1
                    continue
                if empty_count:
                    row.append(str(empty_count))
                    empty_count = 0
                row.append(piece_symbol(piece))
            if empty_count:
                row.append(str(empty_count))
            rows.append("".join(row))
        return "/".join(rows)

    def fen(self) -> str:
        castling = self._castling_fen()
        ep = "-" if self._ep_square == NO_SQUARE else square_name(self._ep_square)
        side = "w" if self._side_to_move == WHITE else "b"
        return (
            f"{self.board_fen()} {side} {castling} {ep} "
            f"{self._halfmove_clock} {self._fullmove_number}"
        )

    def _castling_fen(self) -> str:
        if self._castling_rights == 0:
            return "-"
        result = []
        if self._castling_rights & WHITE_KINGSIDE:
            result.append("K")
        if self._castling_rights & WHITE_QUEENSIDE:
            result.append("Q")
        if self._castling_rights & BLACK_KINGSIDE:
            result.append("k")
        if self._castling_rights & BLACK_QUEENSIDE:
            result.append("q")
        return "".join(result)

    def piece_at(self, square: int) -> int:
        return self._squares[square]

    def piece_type_at(self, square: int) -> int:
        return piece_type(self._squares[square])

    def piece_map(self) -> dict[int, int]:
        return {square: piece for square, piece in enumerate(self._squares) if piece != NO_PIECE}

    def pieces(self, piece: int, color: int) -> int:
        return self._piece_bitboards[piece_code(color, piece)]

    def king_square(self, color: int) -> int:
        return self._king_squares[color]

    def king(self, color: int) -> int:
        return self.king_square(color)

    def attackers_to(
        self,
        square: int,
        color: int | None = None,
        occupied: int | None = None,
    ) -> int:
        if occupied is None:
            occupied = self._occupied

        piece_bitboards = self._piece_bitboards
        if color == WHITE:
            return (
                (PAWN_ATTACKS[BLACK][square] & piece_bitboards[PAWN])
                | (KNIGHT_ATTACKS[square] & piece_bitboards[KNIGHT])
                | (KING_ATTACKS[square] & piece_bitboards[KING])
                | (
                    bishop_attacks(square, occupied)
                    & (piece_bitboards[BISHOP] | piece_bitboards[QUEEN])
                )
                | (
                    rook_attacks(square, occupied)
                    & (piece_bitboards[ROOK] | piece_bitboards[QUEEN])
                )
            )
        if color == BLACK:
            return (
                (PAWN_ATTACKS[WHITE][square] & piece_bitboards[PAWN + 6])
                | (KNIGHT_ATTACKS[square] & piece_bitboards[KNIGHT + 6])
                | (KING_ATTACKS[square] & piece_bitboards[KING + 6])
                | (
                    bishop_attacks(square, occupied)
                    & (piece_bitboards[BISHOP + 6] | piece_bitboards[QUEEN + 6])
                )
                | (
                    rook_attacks(square, occupied)
                    & (piece_bitboards[ROOK + 6] | piece_bitboards[QUEEN + 6])
                )
            )

        white_attackers = (
            (PAWN_ATTACKS[BLACK][square] & piece_bitboards[PAWN])
            | (KNIGHT_ATTACKS[square] & piece_bitboards[KNIGHT])
            | (KING_ATTACKS[square] & piece_bitboards[KING])
            | (
                bishop_attacks(square, occupied)
                & (piece_bitboards[BISHOP] | piece_bitboards[QUEEN])
            )
            | (rook_attacks(square, occupied) & (piece_bitboards[ROOK] | piece_bitboards[QUEEN]))
        )
        black_attackers = (
            (PAWN_ATTACKS[WHITE][square] & piece_bitboards[PAWN + 6])
            | (KNIGHT_ATTACKS[square] & piece_bitboards[KNIGHT + 6])
            | (KING_ATTACKS[square] & piece_bitboards[KING + 6])
            | (
                bishop_attacks(square, occupied)
                & (piece_bitboards[BISHOP + 6] | piece_bitboards[QUEEN + 6])
            )
            | (
                rook_attacks(square, occupied)
                & (piece_bitboards[ROOK + 6] | piece_bitboards[QUEEN + 6])
            )
        )
        return white_attackers | black_attackers

    def is_square_attacked(self, square: int, by_color: int) -> bool:
        piece_bitboards = self._piece_bitboards
        offset = by_color * 6
        occupied = self._occupied
        if PAWN_ATTACKS[by_color ^ 1][square] & piece_bitboards[PAWN + offset]:
            return True
        if KNIGHT_ATTACKS[square] & piece_bitboards[KNIGHT + offset]:
            return True
        if KING_ATTACKS[square] & piece_bitboards[KING + offset]:
            return True
        if bishop_attacks(square, occupied) & (
            piece_bitboards[BISHOP + offset] | piece_bitboards[QUEEN + offset]
        ):
            return True
        return bool(
            rook_attacks(square, occupied)
            & (piece_bitboards[ROOK + offset] | piece_bitboards[QUEEN + offset])
        )

    def is_check(self) -> bool:
        king = self.king_square(self._side_to_move)
        return king != NO_SQUARE and self.is_square_attacked(king, opposite(self._side_to_move))

    def _checkers_to_king(self) -> int:
        us = self._side_to_move
        them_offset = (us ^ 1) * 6
        king = self._king_squares[us]
        occupied = self._occupied
        piece_bitboards = self._piece_bitboards
        return (
            (PAWN_ATTACKS[us][king] & piece_bitboards[PAWN + them_offset])
            | (KNIGHT_ATTACKS[king] & piece_bitboards[KNIGHT + them_offset])
            | (
                bishop_attacks(king, occupied)
                & (piece_bitboards[BISHOP + them_offset] | piece_bitboards[QUEEN + them_offset])
            )
            | (
                rook_attacks(king, occupied)
                & (piece_bitboards[ROOK + them_offset] | piece_bitboards[QUEEN + them_offset])
            )
        )

    @staticmethod
    def _between(source: int, target: int) -> int:
        source_rank, source_file = divmod(source, 8)
        target_rank, target_file = divmod(target, 8)
        rank_delta = 0 if target_rank == source_rank else (1 if target_rank > source_rank else -1)
        file_delta = 0 if target_file == source_file else (1 if target_file > source_file else -1)

        if rank_delta != 0 and file_delta != 0:
            if abs(target_rank - source_rank) != abs(target_file - source_file):
                return 0
        elif rank_delta == 0 and file_delta == 0:
            return 0

        between = 0
        rank = source_rank + rank_delta
        file_index = source_file + file_delta
        while 0 <= rank < 8 and 0 <= file_index < 8:
            square = rank * 8 + file_index
            if square == target:
                break
            between |= BB_SQUARES[square]
            rank += rank_delta
            file_index += file_delta
        return between

    def _pinned_pieces(self, color: int) -> int:
        king = self._king_squares[color]
        if king == NO_SQUARE:
            return 0

        pinned = 0
        king_rank, king_file = divmod(king, 8)
        enemy = color ^ 1
        squares = self._squares
        directions = (
            (1, 0, ROOK, QUEEN),
            (-1, 0, ROOK, QUEEN),
            (0, 1, ROOK, QUEEN),
            (0, -1, ROOK, QUEEN),
            (1, 1, BISHOP, QUEEN),
            (1, -1, BISHOP, QUEEN),
            (-1, 1, BISHOP, QUEEN),
            (-1, -1, BISHOP, QUEEN),
        )

        for rank_delta, file_delta, slider, queen in directions:
            blocker = NO_SQUARE
            rank = king_rank + rank_delta
            file_index = king_file + file_delta
            while 0 <= rank < 8 and 0 <= file_index < 8:
                square = rank * 8 + file_index
                piece = squares[square]
                if piece == NO_PIECE:
                    rank += rank_delta
                    file_index += file_delta
                    continue

                piece_is_black = piece > KING
                piece_color_value = BLACK if piece_is_black else WHITE
                if blocker == NO_SQUARE:
                    if piece_color_value == color:
                        blocker = square
                        rank += rank_delta
                        file_index += file_delta
                        continue
                    break

                if piece_color_value == color:
                    break
                piece_kind = piece - 6 if piece_is_black else piece
                if piece_color_value == enemy and (piece_kind == slider or piece_kind == queen):  # noqa: PLR1714, SIM109
                    pinned |= BB_SQUARES[blocker]
                break
        return pinned

    def generate_pseudo_legal_moves(  # noqa: C901, PLR0912, PLR0914, PLR0915
        self,
        *,
        captures_only: bool = False,
    ) -> list[Move]:
        us = self._side_to_move
        them = us ^ 1
        us_offset = us * 6
        them_offset = them * 6
        own = self._occupancy_by_color[us]
        enemy = self._occupancy_by_color[them]
        enemy_king = self._piece_bitboards[KING + them_offset]
        enemy_targets = enemy & ~enemy_king
        empty = BB_ALL ^ self._occupied
        blocked = own | enemy_king
        occupied = self._occupied
        piece_bitboards = self._piece_bitboards
        moves: list[Move] = []
        append = moves.append

        pawns = piece_bitboards[PAWN + us_offset]
        if us == WHITE:
            if not captures_only:
                one_step = (pawns << 8) & empty
                for target in iter_bits(one_step & ~BB_RANK_8):
                    append((target - 8) | (target << 6))
                for target in iter_bits(one_step & BB_RANK_8):
                    source = target - 8
                    for promotion in PROMOTION_PIECES:
                        append(source | (target << 6) | (promotion << 12) | (PROMOTION << 15))
                two_step = ((one_step & BB_RANK_3) << 8) & empty
                for target in iter_bits(two_step):
                    append((target - 16) | (target << 6) | (DOUBLE_PAWN_PUSH << 15))

            left_captures = ((pawns & ~BB_FILE_A) << 7) & enemy_targets
            right_captures = ((pawns & ~BB_FILE_H) << 9) & enemy_targets
            self._append_pawn_captures(moves, left_captures, -7)
            self._append_pawn_captures(moves, right_captures, -9)
        else:
            if not captures_only:
                one_step = (pawns >> 8) & empty
                for target in iter_bits(one_step & ~BB_RANK_1):
                    append((target + 8) | (target << 6))
                for target in iter_bits(one_step & BB_RANK_1):
                    source = target + 8
                    for promotion in PROMOTION_PIECES:
                        append(source | (target << 6) | (promotion << 12) | (PROMOTION << 15))
                two_step = ((one_step & BB_RANK_6) >> 8) & empty
                for target in iter_bits(two_step):
                    append((target + 16) | (target << 6) | (DOUBLE_PAWN_PUSH << 15))

            left_captures = ((pawns & ~BB_FILE_A) >> 9) & enemy_targets
            right_captures = ((pawns & ~BB_FILE_H) >> 7) & enemy_targets
            self._append_pawn_captures(moves, left_captures, 9)
            self._append_pawn_captures(moves, right_captures, 7)

        if self._ep_square != NO_SQUARE:
            attackers = PAWN_ATTACKS[them][self._ep_square] & pawns
            for source in iter_bits(attackers):
                append(source | (self._ep_square << 6) | ((CAPTURE | EN_PASSANT) << 15))

        pieces_to_scan = piece_bitboards[KNIGHT + us_offset]
        while pieces_to_scan:
            source_bit = pieces_to_scan & -pieces_to_scan
            source = source_bit.bit_length() - 1
            targets = KNIGHT_ATTACKS[source] & ~blocked
            if captures_only:
                targets &= enemy_targets
            while targets:
                target_bit = targets & -targets
                target = target_bit.bit_length() - 1
                flags = CAPTURE if target_bit & enemy_targets else 0
                append(source | (target << 6) | (flags << 15))
                targets ^= target_bit
            pieces_to_scan ^= source_bit

        pieces_to_scan = piece_bitboards[BISHOP + us_offset]
        while pieces_to_scan:
            source_bit = pieces_to_scan & -pieces_to_scan
            source = source_bit.bit_length() - 1
            targets = bishop_attacks(source, occupied) & ~blocked
            if captures_only:
                targets &= enemy_targets
            while targets:
                target_bit = targets & -targets
                target = target_bit.bit_length() - 1
                flags = CAPTURE if target_bit & enemy_targets else 0
                append(source | (target << 6) | (flags << 15))
                targets ^= target_bit
            pieces_to_scan ^= source_bit

        pieces_to_scan = piece_bitboards[ROOK + us_offset]
        while pieces_to_scan:
            source_bit = pieces_to_scan & -pieces_to_scan
            source = source_bit.bit_length() - 1
            targets = rook_attacks(source, occupied) & ~blocked
            if captures_only:
                targets &= enemy_targets
            while targets:
                target_bit = targets & -targets
                target = target_bit.bit_length() - 1
                flags = CAPTURE if target_bit & enemy_targets else 0
                append(source | (target << 6) | (flags << 15))
                targets ^= target_bit
            pieces_to_scan ^= source_bit

        pieces_to_scan = piece_bitboards[QUEEN + us_offset]
        while pieces_to_scan:
            source_bit = pieces_to_scan & -pieces_to_scan
            source = source_bit.bit_length() - 1
            targets = queen_attacks(source, occupied) & ~blocked
            if captures_only:
                targets &= enemy_targets
            while targets:
                target_bit = targets & -targets
                target = target_bit.bit_length() - 1
                flags = CAPTURE if target_bit & enemy_targets else 0
                append(source | (target << 6) | (flags << 15))
                targets ^= target_bit
            pieces_to_scan ^= source_bit

        pieces_to_scan = piece_bitboards[KING + us_offset]
        while pieces_to_scan:
            source_bit = pieces_to_scan & -pieces_to_scan
            source = source_bit.bit_length() - 1
            targets = KING_ATTACKS[source] & ~blocked
            if captures_only:
                targets &= enemy_targets
            while targets:
                target_bit = targets & -targets
                target = target_bit.bit_length() - 1
                flags = CAPTURE if target_bit & enemy_targets else 0
                append(source | (target << 6) | (flags << 15))
                targets ^= target_bit
            pieces_to_scan ^= source_bit

        if not captures_only:
            moves.extend(self._generate_castling_moves(us))

        return moves

    @staticmethod
    def _append_pawn_captures(moves: list[Move], targets: int, source_delta: int) -> None:
        normal_targets = targets & ~(BB_RANK_1 | BB_RANK_8)
        while normal_targets:
            target_bit = normal_targets & -normal_targets
            target = target_bit.bit_length() - 1
            moves.append((target + source_delta) | (target << 6) | (CAPTURE << 15))
            normal_targets ^= target_bit

        promotion_targets = targets & (BB_RANK_1 | BB_RANK_8)
        while promotion_targets:
            target_bit = promotion_targets & -promotion_targets
            target = target_bit.bit_length() - 1
            source = target + source_delta
            for promotion in PROMOTION_PIECES:
                moves.append(  # noqa: PERF401
                    source | (target << 6) | (promotion << 12) | ((CAPTURE | PROMOTION) << 15)
                )
            promotion_targets ^= target_bit

    @staticmethod
    def _append_targets(
        moves: list[Move],
        source: int,
        targets: int,
        enemy_targets: int,
    ) -> None:
        for target in iter_bits(targets):
            flags = CAPTURE if BB_SQUARES[target] & enemy_targets else 0
            moves.append(source | (target << 6) | (flags << 15))

    def _generate_pawn_moves(
        self,
        color: int,
        enemy_targets: int,
        empty: int,
        *,
        captures_only: bool,
    ) -> Iterator[Move]:
        pawns = self._piece_bitboards[piece_code(color, PAWN)]
        if color == WHITE:
            if not captures_only:
                one_step = (pawns << 8) & empty
                yield from self._generate_pawn_pushes(one_step & ~BB_RANK_8, -8)
                yield from self._generate_pawn_promotions(one_step & BB_RANK_8, -8, 0)
                two_step = ((one_step & BB_RANK_3) << 8) & empty
                for target in iter_bits(two_step):
                    yield encode_move(target - 16, target, flags=DOUBLE_PAWN_PUSH)
            left_captures = ((pawns & ~BB_FILE_A) << 7) & enemy_targets
            right_captures = ((pawns & ~BB_FILE_H) << 9) & enemy_targets
            yield from self._generate_pawn_captures(left_captures, -7)
            yield from self._generate_pawn_captures(right_captures, -9)
        else:
            if not captures_only:
                one_step = (pawns >> 8) & empty
                yield from self._generate_pawn_pushes(one_step & ~BB_RANK_1, 8)
                yield from self._generate_pawn_promotions(one_step & BB_RANK_1, 8, 0)
                two_step = ((one_step & BB_RANK_6) >> 8) & empty
                for target in iter_bits(two_step):
                    yield encode_move(target + 16, target, flags=DOUBLE_PAWN_PUSH)
            left_captures = ((pawns & ~BB_FILE_A) >> 9) & enemy_targets
            right_captures = ((pawns & ~BB_FILE_H) >> 7) & enemy_targets
            yield from self._generate_pawn_captures(left_captures, 9)
            yield from self._generate_pawn_captures(right_captures, 7)

        if self._ep_square != NO_SQUARE:
            attackers = PAWN_ATTACKS[opposite(color)][self._ep_square] & pawns
            for source in iter_bits(attackers):
                yield encode_move(source, self._ep_square, flags=CAPTURE | EN_PASSANT)

    @staticmethod
    def _generate_pawn_pushes(targets: int, source_delta: int) -> Iterator[Move]:
        for target in iter_bits(targets):
            yield encode_move(target + source_delta, target)

    @staticmethod
    def _generate_pawn_captures(targets: int, source_delta: int) -> Iterator[Move]:
        promotion_targets = targets & (BB_RANK_1 | BB_RANK_8)
        normal_targets = targets & ~promotion_targets
        for target in iter_bits(normal_targets):
            yield encode_move(target + source_delta, target, flags=CAPTURE)
        yield from Board._generate_pawn_promotions(promotion_targets, source_delta, CAPTURE)

    @staticmethod
    def _generate_pawn_promotions(targets: int, source_delta: int, flags: int) -> Iterator[Move]:
        for target in iter_bits(targets):
            source = target + source_delta
            for promotion in PROMOTION_PIECES:
                yield encode_move(source, target, promotion, flags)

    def _generate_leaper_moves(
        self,
        piece: int,
        attacks: tuple[int, ...],
        blocked: int,
        enemy_targets: int,
        *,
        captures_only: bool,
    ) -> Iterator[Move]:
        for source in iter_bits(self._piece_bitboards[piece]):
            targets = attacks[source] & ~blocked
            if captures_only:
                targets &= enemy_targets
            yield from self._targets_to_moves(source, targets, enemy_targets)

    def _generate_slider_moves(
        self,
        piece: int,
        blocked: int,
        enemy_targets: int,
        *,
        captures_only: bool,
    ) -> Iterator[Move]:
        attack_function = {
            BISHOP: bishop_attacks,
            ROOK: rook_attacks,
            QUEEN: queen_attacks,
        }[piece_type(piece)]
        for source in iter_bits(self._piece_bitboards[piece]):
            targets = attack_function(source, self._occupied) & ~blocked
            if captures_only:
                targets &= enemy_targets
            yield from self._targets_to_moves(source, targets, enemy_targets)

    @staticmethod
    def _targets_to_moves(source: int, targets: int, enemy_targets: int) -> Iterator[Move]:
        for target in iter_bits(targets):
            flags = CAPTURE if BB_SQUARES[target] & enemy_targets else 0
            yield encode_move(source, target, flags=flags)

    def _generate_castling_moves(self, color: int) -> Iterator[Move]:
        enemy = color ^ 1
        if color == WHITE:
            if (
                self._castling_rights & WHITE_KINGSIDE  # noqa: PLR0916
                and self._squares[E1] == KING
                and self._squares[H1] == ROOK
                and not (self._occupied & (BB_SQUARES[F1] | BB_SQUARES[G1]))
                and not self.is_square_attacked(E1, enemy)
                and not self.is_square_attacked(F1, enemy)
                and not self.is_square_attacked(G1, enemy)
            ):
                yield encode_move(E1, G1, flags=CASTLING)
            if (
                self._castling_rights & WHITE_QUEENSIDE  # noqa: PLR0916
                and self._squares[E1] == KING
                and self._squares[A1] == ROOK
                and not (self._occupied & (BB_SQUARES[B1] | BB_SQUARES[C1] | BB_SQUARES[D1]))
                and not self.is_square_attacked(E1, enemy)
                and not self.is_square_attacked(D1, enemy)
                and not self.is_square_attacked(C1, enemy)
            ):
                yield encode_move(E1, C1, flags=CASTLING)
            return

        if (
            self._castling_rights & BLACK_KINGSIDE  # noqa: PLR0916
            and self._squares[E8] == KING + 6
            and self._squares[H8] == ROOK + 6
            and not (self._occupied & (BB_SQUARES[F8] | BB_SQUARES[G8]))
            and not self.is_square_attacked(E8, enemy)
            and not self.is_square_attacked(F8, enemy)
            and not self.is_square_attacked(G8, enemy)
        ):
            yield encode_move(E8, G8, flags=CASTLING)
        if (
            self._castling_rights & BLACK_QUEENSIDE  # noqa: PLR0916
            and self._squares[E8] == KING + 6
            and self._squares[A8] == ROOK + 6
            and not (self._occupied & (BB_SQUARES[B8] | BB_SQUARES[C8] | BB_SQUARES[D8]))
            and not self.is_square_attacked(E8, enemy)
            and not self.is_square_attacked(D8, enemy)
            and not self.is_square_attacked(C8, enemy)
        ):
            yield encode_move(E8, C8, flags=CASTLING)

    def generate_legal_moves(self, *, captures_only: bool = False) -> list[Move]:
        checkers = self._checkers_to_king()
        if checkers:
            return self._generate_evasions(checkers, captures_only=captures_only)

        king = self._king_squares[self._side_to_move]
        pinned = self._pinned_pieces(self._side_to_move)
        legal_moves = []
        append = legal_moves.append
        for move in self.generate_pseudo_legal_moves(captures_only=captures_only):
            move_value = int(move)
            source = move_value & 0x3F
            if source == king or BB_SQUARES[source] & pinned or move_value >> 15 & EN_PASSANT:
                if self._is_safe_after(move):
                    append(move)
            else:
                append(move)
        return legal_moves

    def generate_legal_captures(self) -> list[Move]:
        return [
            move for move in self._generate_pseudo_legal_captures() if self._is_safe_after(move)
        ]

    def _generate_pseudo_legal_captures(self) -> list[Move]:  # noqa: C901, PLR0912, PLR0914, PLR0915
        us = self._side_to_move
        them = us ^ 1
        us_offset = us * 6
        piece_bitboards = self._piece_bitboards
        enemy = self._occupancy_by_color[them] & ~piece_bitboards[KING + them * 6]
        occupied = self._occupied
        moves: list[Move] = []
        append = moves.append

        pawns = piece_bitboards[PAWN + us_offset]
        if us == WHITE:
            promo_pawns = pawns & BB_RANK_7
            pawn_dir = 8
            push_promotions = ((promo_pawns << 8) & BB_ALL) & (BB_ALL ^ occupied)
            left_captures = ((pawns & ~BB_FILE_A) << 7) & enemy
            while left_captures:
                target_bit = left_captures & -left_captures
                target = target_bit.bit_length() - 1
                source = target - 7
                if target_bit & BB_RANK_8:
                    base = source | (target << 6) | ((CAPTURE | PROMOTION) << 15)
                    append(base | (QUEEN << 12))
                    append(base | (ROOK << 12))
                    append(base | (BISHOP << 12))
                    append(base | (KNIGHT << 12))
                else:
                    append(source | (target << 6) | (CAPTURE << 15))
                left_captures ^= target_bit

            right_captures = ((pawns & ~BB_FILE_H) << 9) & enemy
            while right_captures:
                target_bit = right_captures & -right_captures
                target = target_bit.bit_length() - 1
                source = target - 9
                if target_bit & BB_RANK_8:
                    base = source | (target << 6) | ((CAPTURE | PROMOTION) << 15)
                    append(base | (QUEEN << 12))
                    append(base | (ROOK << 12))
                    append(base | (BISHOP << 12))
                    append(base | (KNIGHT << 12))
                else:
                    append(source | (target << 6) | (CAPTURE << 15))
                right_captures ^= target_bit
        else:
            promo_pawns = pawns & BB_RANK_2
            pawn_dir = -8
            push_promotions = (promo_pawns >> 8) & (BB_ALL ^ occupied)
            left_captures = ((pawns & ~BB_FILE_A) >> 9) & enemy
            while left_captures:
                target_bit = left_captures & -left_captures
                target = target_bit.bit_length() - 1
                source = target + 9
                if target_bit & BB_RANK_1:
                    base = source | (target << 6) | ((CAPTURE | PROMOTION) << 15)
                    append(base | (QUEEN << 12))
                    append(base | (ROOK << 12))
                    append(base | (BISHOP << 12))
                    append(base | (KNIGHT << 12))
                else:
                    append(source | (target << 6) | (CAPTURE << 15))
                left_captures ^= target_bit

            right_captures = ((pawns & ~BB_FILE_H) >> 7) & enemy
            while right_captures:
                target_bit = right_captures & -right_captures
                target = target_bit.bit_length() - 1
                source = target + 7
                if target_bit & BB_RANK_1:
                    base = source | (target << 6) | ((CAPTURE | PROMOTION) << 15)
                    append(base | (QUEEN << 12))
                    append(base | (ROOK << 12))
                    append(base | (BISHOP << 12))
                    append(base | (KNIGHT << 12))
                else:
                    append(source | (target << 6) | (CAPTURE << 15))
                right_captures ^= target_bit

        while push_promotions:
            target_bit = push_promotions & -push_promotions
            target = target_bit.bit_length() - 1
            source = target - pawn_dir
            base = source | (target << 6) | (PROMOTION << 15)
            append(base | (QUEEN << 12))
            append(base | (ROOK << 12))
            append(base | (BISHOP << 12))
            append(base | (KNIGHT << 12))
            push_promotions ^= target_bit

        if self._ep_square != NO_SQUARE:
            capturers = PAWN_ATTACKS[them][self._ep_square] & pawns
            while capturers:
                source_bit = capturers & -capturers
                source = source_bit.bit_length() - 1
                append(source | (self._ep_square << 6) | ((CAPTURE | EN_PASSANT) << 15))
                capturers ^= source_bit

        pieces_to_scan = piece_bitboards[KNIGHT + us_offset]
        while pieces_to_scan:
            source_bit = pieces_to_scan & -pieces_to_scan
            source = source_bit.bit_length() - 1
            targets = KNIGHT_ATTACKS[source] & enemy
            while targets:
                target_bit = targets & -targets
                target = target_bit.bit_length() - 1
                append(source | (target << 6) | (CAPTURE << 15))
                targets ^= target_bit
            pieces_to_scan ^= source_bit

        pieces_to_scan = piece_bitboards[BISHOP + us_offset]
        while pieces_to_scan:
            source_bit = pieces_to_scan & -pieces_to_scan
            source = source_bit.bit_length() - 1
            if BISHOP_RAYS[source] & enemy:
                targets = bishop_attacks(source, occupied) & enemy
                while targets:
                    target_bit = targets & -targets
                    target = target_bit.bit_length() - 1
                    append(source | (target << 6) | (CAPTURE << 15))
                    targets ^= target_bit
            pieces_to_scan ^= source_bit

        pieces_to_scan = piece_bitboards[ROOK + us_offset]
        while pieces_to_scan:
            source_bit = pieces_to_scan & -pieces_to_scan
            source = source_bit.bit_length() - 1
            if ROOK_RAYS[source] & enemy:
                targets = rook_attacks(source, occupied) & enemy
                while targets:
                    target_bit = targets & -targets
                    target = target_bit.bit_length() - 1
                    append(source | (target << 6) | (CAPTURE << 15))
                    targets ^= target_bit
            pieces_to_scan ^= source_bit

        pieces_to_scan = piece_bitboards[QUEEN + us_offset]
        while pieces_to_scan:
            source_bit = pieces_to_scan & -pieces_to_scan
            source = source_bit.bit_length() - 1
            targets = 0
            if BISHOP_RAYS[source] & enemy:
                targets |= bishop_attacks(source, occupied)
            if ROOK_RAYS[source] & enemy:
                targets |= rook_attacks(source, occupied)
            targets &= enemy
            while targets:
                target_bit = targets & -targets
                target = target_bit.bit_length() - 1
                append(source | (target << 6) | (CAPTURE << 15))
                targets ^= target_bit
            pieces_to_scan ^= source_bit

        source = self._king_squares[us]
        targets = KING_ATTACKS[source] & enemy
        while targets:
            target_bit = targets & -targets
            target = target_bit.bit_length() - 1
            append(source | (target << 6) | (CAPTURE << 15))
            targets ^= target_bit

        return moves

    def _generate_evasions(  # noqa: C901
        self,
        checkers: int,
        *,
        captures_only: bool,
    ) -> list[Move]:
        us = self._side_to_move
        king = self._king_squares[us]
        own = self._occupancy_by_color[us]
        enemy = self._occupancy_by_color[us ^ 1]
        enemy_king = self._piece_bitboards[KING + (us ^ 1) * 6]
        legal: list[Move] = []
        append = legal.append

        king_targets = KING_ATTACKS[king] & ~(own | enemy_king)
        if captures_only:
            king_targets &= enemy
        while king_targets:
            target_bit = king_targets & -king_targets
            target = target_bit.bit_length() - 1
            move = king | (target << 6) | ((CAPTURE if target_bit & enemy else 0) << 15)
            if self._is_safe_after(move):
                append(move)
            king_targets ^= target_bit

        if checkers & (checkers - 1):
            return legal

        checker = (checkers & -checkers).bit_length() - 1
        block_mask = self._between(king, checker) | BB_SQUARES[checker]

        for move in self.generate_pseudo_legal_moves(captures_only=captures_only):
            move_value = int(move)
            source = move_value & 0x3F
            if source == king:
                continue
            target = (move_value >> 6) & 0x3F
            if not (BB_SQUARES[target] & block_mask):
                if move_value >> 15 & EN_PASSANT:
                    captured_square = target - 8 if us == WHITE else target + 8
                    if not (BB_SQUARES[captured_square] & checkers):
                        continue
                else:
                    continue
            if self._is_safe_after(move):
                append(move)

        return legal

    def _is_safe_after(self, move: Move) -> bool:  # noqa: PLR0911, PLR0914
        color = self._side_to_move
        move_value = int(move)
        source = move_value & 0x3F
        target = (move_value >> 6) & 0x3F
        flags = move_value >> 15
        moved_piece = self._squares[source]

        if flags & CASTLING:
            return True

        source_bit = BB_SQUARES[source]
        target_bit = BB_SQUARES[target]
        occupied = (self._occupied & ~source_bit) | target_bit

        captured_bit = 0
        if flags & EN_PASSANT:
            captured_square = target - 8 if color == WHITE else target + 8
            captured_bit = BB_SQUARES[captured_square]
            occupied &= ~captured_bit
        elif self._squares[target] != NO_PIECE:
            captured_bit = target_bit

        king = (
            target if moved_piece == KING or moved_piece == KING + 6 else self._king_squares[color]
        )
        if king == NO_SQUARE:
            return False

        piece_bitboards = self._piece_bitboards
        enemy_offset = (color ^ 1) * 6
        capture_mask = BB_ALL ^ captured_bit

        if piece_bitboards[KNIGHT + enemy_offset] & capture_mask & KNIGHT_ATTACKS[king]:
            return False
        if piece_bitboards[PAWN + enemy_offset] & capture_mask & PAWN_ATTACKS[color][king]:
            return False
        if piece_bitboards[KING + enemy_offset] & KING_ATTACKS[king]:
            return False

        bishops_queens = (
            piece_bitboards[BISHOP + enemy_offset] | piece_bitboards[QUEEN + enemy_offset]
        ) & capture_mask
        if bishops_queens and bishop_attacks(king, occupied) & bishops_queens:
            return False

        rooks_queens = (
            piece_bitboards[ROOK + enemy_offset] | piece_bitboards[QUEEN + enemy_offset]
        ) & capture_mask
        return not (rooks_queens and rook_attacks(king, occupied) & rooks_queens)

    def is_legal(self, move: Move) -> bool:
        return any(same_move(move, legal_move) for legal_move in self.generate_legal_moves())

    def parse_uci(self, value: str) -> Move:
        if value == "0000":
            return NULL_MOVE
        source, target, promotion = parse_uci_squares(value)
        moved_piece = self._squares[source]
        flags = 0
        if moved_piece == NO_PIECE:
            msg = f"No piece on source square for UCI move: {value}"
            raise ValueError(msg)
        if self._squares[target] != NO_PIECE:
            flags |= CAPTURE
        if piece_type(moved_piece) == PAWN:
            if target == self._ep_square and file_of(source) != file_of(target):
                flags |= CAPTURE | EN_PASSANT
            if abs(target - source) == 16:
                flags |= DOUBLE_PAWN_PUSH
        if piece_type(moved_piece) == KING and abs(target - source) == 2:
            flags |= CASTLING
        return encode_move(source, target, promotion, flags)

    def legal_move_from_uci(self, value: str) -> Move:
        move = self.parse_uci(value)
        if move == NULL_MOVE:
            return move
        for legal_move in self.generate_legal_moves():
            if same_move(move, legal_move):
                return legal_move
        msg = f"Illegal UCI move in current position: {value}"
        raise ValueError(msg)

    def push_uci(self, value: str) -> Move:
        move = self.legal_move_from_uci(value)
        self.push(move)
        return move

    def push(self, move: Move) -> None:  # noqa: C901, PLR0912, PLR0914, PLR0915
        if move == NULL_MOVE:
            self.push_null()
            return

        move_value = int(move)
        source = move_value & 0x3F
        target = (move_value >> 6) & 0x3F
        promotion = (move_value >> 12) & 0x7
        flags = move_value >> 15
        side = self._side_to_move
        moved_piece = self._squares[source]
        captured_square = NO_SQUARE
        if flags & EN_PASSANT:
            captured_square = target - 8 if side == WHITE else target + 8
        elif self._squares[target] != NO_PIECE:
            captured_square = target
        captured_piece = (
            self._squares[captured_square] if captured_square != NO_SQUARE else NO_PIECE
        )
        old_ep_square = self._ep_square
        state = (
            move,
            moved_piece,
            captured_piece,
            captured_square,
            self._castling_rights,
            self._ep_square,
            self._halfmove_clock,
            self._fullmove_number,
            self._zobrist_key,
        )
        self._history.append(state)

        if old_ep_square != NO_SQUARE:
            old_ep_hash_file = self._ep_hash_file(old_ep_square, side)
            if old_ep_hash_file != NO_SQUARE:
                self._zobrist_key ^= EN_PASSANT_FILE_KEYS[old_ep_hash_file]
        self._ep_square = NO_SQUARE

        if captured_piece != NO_PIECE:
            self._remove_piece(captured_piece, captured_square)

        if promotion:
            placed_piece = promotion + (6 if moved_piece > KING else 0)
            self._remove_piece(moved_piece, source)
            self._put_piece(placed_piece, target)
        else:
            move_bits = BB_SQUARES[source] | BB_SQUARES[target]
            move_color = BLACK if moved_piece > KING else WHITE
            self._squares[source] = NO_PIECE
            self._squares[target] = moved_piece
            if moved_piece == KING or moved_piece == KING + 6:
                self._king_squares[move_color] = target
            self._piece_bitboards[moved_piece] ^= move_bits
            self._occupancy_by_color[move_color] ^= move_bits
            self._occupied ^= move_bits
            self._zobrist_key ^= PIECE_KEYS[moved_piece][source] ^ PIECE_KEYS[moved_piece][target]

        if flags & CASTLING:
            self._push_castling_rook(target)

        old_rights = self._castling_rights
        self._castling_rights &= CASTLING_RIGHTS_MASKS[source] & CASTLING_RIGHTS_MASKS[target]
        if old_rights != self._castling_rights:
            self._zobrist_key ^= CASTLING_KEYS[old_rights] ^ CASTLING_KEYS[self._castling_rights]

        if flags & DOUBLE_PAWN_PUSH:
            self._ep_square = (source + target) // 2

        is_irreversible = (
            moved_piece == PAWN or moved_piece == PAWN + 6 or captured_piece != NO_PIECE
        )
        self._halfmove_clock = 0 if is_irreversible else self._halfmove_clock + 1
        if side == BLACK:
            self._fullmove_number += 1

        self._side_to_move = side ^ 1
        self._zobrist_key ^= SIDE_TO_MOVE_KEY

        if self._ep_square != NO_SQUARE:
            new_ep_hash_file = self._ep_hash_file(self._ep_square, self._side_to_move)
            if new_ep_hash_file != NO_SQUARE:
                self._zobrist_key ^= EN_PASSANT_FILE_KEYS[new_ep_hash_file]
        self._key_history.append(self._zobrist_key)

    def push_null(self) -> None:
        old_ep_hash_file = self._ep_hash_file(self._ep_square, self._side_to_move)
        self._history.append((
            NULL_MOVE,
            NO_PIECE,
            NO_PIECE,
            NO_SQUARE,
            self._castling_rights,
            self._ep_square,
            self._halfmove_clock,
            self._fullmove_number,
            self._zobrist_key,
        ))
        if old_ep_hash_file != NO_SQUARE:
            self._zobrist_key ^= EN_PASSANT_FILE_KEYS[old_ep_hash_file]
        self._ep_square = NO_SQUARE
        self._halfmove_clock += 1
        if self._side_to_move == BLACK:
            self._fullmove_number += 1
        self._side_to_move = opposite(self._side_to_move)
        self._zobrist_key ^= SIDE_TO_MOVE_KEY
        self._key_history.append(self._zobrist_key)

    def pop(self) -> Move:  # noqa: PLR0914, PLR0915
        state = self._history.pop()
        if self._key_history:
            self._key_history.pop()

        if state[0] == NULL_MOVE:
            self._side_to_move ^= 1
            self._castling_rights = state[4]
            self._ep_square = state[5]
            self._halfmove_clock = state[6]
            self._fullmove_number = state[7]
            self._zobrist_key = state[8]
            return state[0]

        move_value = int(state[0])
        source = move_value & 0x3F
        target = (move_value >> 6) & 0x3F
        promotion = (move_value >> 12) & 0x7
        flags = move_value >> 15
        if promotion:
            promoted_piece = self._squares[target]
            move_color = BLACK if promoted_piece > KING else WHITE
            target_bit = BB_SQUARES[target]
            source_bit = BB_SQUARES[source]
            self._squares[target] = NO_PIECE
            self._squares[source] = state[1]
            self._piece_bitboards[promoted_piece] ^= target_bit
            self._piece_bitboards[state[1]] |= source_bit
            self._occupancy_by_color[move_color] ^= target_bit
            self._occupancy_by_color[move_color] |= source_bit
            self._occupied ^= target_bit
            self._occupied |= source_bit
        else:
            move_bits = BB_SQUARES[target] | BB_SQUARES[source]
            moved_piece = state[1]
            move_color = BLACK if moved_piece > KING else WHITE
            self._squares[target] = NO_PIECE
            self._squares[source] = moved_piece
            if moved_piece == KING or moved_piece == KING + 6:
                self._king_squares[move_color] = source
            self._piece_bitboards[moved_piece] ^= move_bits
            self._occupancy_by_color[move_color] ^= move_bits
            self._occupied ^= move_bits
        if flags & CASTLING:
            self._pop_castling_rook(target)
        if state[2] != NO_PIECE:
            captured_piece = state[2]
            captured_square = state[3]
            captured_bit = BB_SQUARES[captured_square]
            captured_color = BLACK if captured_piece > KING else WHITE
            self._squares[captured_square] = captured_piece
            self._piece_bitboards[captured_piece] |= captured_bit
            self._occupancy_by_color[captured_color] |= captured_bit
            self._occupied |= captured_bit

        self._side_to_move ^= 1
        self._castling_rights = state[4]
        self._ep_square = state[5]
        self._halfmove_clock = state[6]
        self._fullmove_number = state[7]
        self._zobrist_key = state[8]
        return state[0]

    def _restore_state(self, state: tuple[int, int, int, int, int, int, int, int, int]) -> None:
        self._side_to_move = opposite(self._side_to_move)
        self._castling_rights = state[4]
        self._ep_square = state[5]
        self._halfmove_clock = state[6]
        self._fullmove_number = state[7]
        self._zobrist_key = state[8]

    def _push_castling_rook(self, king_target: int) -> None:
        match king_target:
            case 6:
                self._move_piece(piece_code(WHITE, ROOK), H1, F1)
            case 2:
                self._move_piece(piece_code(WHITE, ROOK), A1, D1)
            case 62:
                self._move_piece(piece_code(BLACK, ROOK), H8, F8)
            case 58:
                self._move_piece(piece_code(BLACK, ROOK), A8, D8)

    def _pop_castling_rook(self, king_target: int) -> None:
        match king_target:
            case 6:
                self._move_piece(piece_code(WHITE, ROOK), F1, H1)
            case 2:
                self._move_piece(piece_code(WHITE, ROOK), D1, A1)
            case 62:
                self._move_piece(piece_code(BLACK, ROOK), F8, H8)
            case 58:
                self._move_piece(piece_code(BLACK, ROOK), D8, A8)

    def _captured_square(self, move: Move) -> int:
        if is_en_passant(move):
            return to_square(move) - 8 if self._side_to_move == WHITE else to_square(move) + 8
        return to_square(move) if self._squares[to_square(move)] != NO_PIECE else NO_SQUARE

    def _update_castling_rights(
        self,
        move: Move,
        moved_piece: int,
        captured_square: int,
        captured_piece: int,
    ) -> None:
        old_rights = self._castling_rights
        source = from_square(move)
        if piece_type(moved_piece) == KING:
            if piece_color(moved_piece) == WHITE:
                self._castling_rights &= ~(WHITE_KINGSIDE | WHITE_QUEENSIDE)
            else:
                self._castling_rights &= ~(BLACK_KINGSIDE | BLACK_QUEENSIDE)
        elif piece_type(moved_piece) == ROOK:
            self._clear_rook_castling_right(source)

        if captured_piece != NO_PIECE and piece_type(captured_piece) == ROOK:
            self._clear_rook_castling_right(captured_square)

        if old_rights != self._castling_rights:
            self._zobrist_key ^= CASTLING_KEYS[old_rights] ^ CASTLING_KEYS[self._castling_rights]

    def _clear_rook_castling_right(self, square: int) -> None:
        match square:
            case 0:
                self._castling_rights &= ~WHITE_QUEENSIDE
            case 7:
                self._castling_rights &= ~WHITE_KINGSIDE
            case 56:
                self._castling_rights &= ~BLACK_QUEENSIDE
            case 63:
                self._castling_rights &= ~BLACK_KINGSIDE

    def _put_piece(self, piece: int, square: int) -> None:
        bit = BB_SQUARES[square]
        color = BLACK if piece > KING else WHITE
        self._squares[square] = piece
        if piece == KING or piece == KING + 6:
            self._king_squares[color] = square
        self._piece_bitboards[piece] |= bit
        self._occupancy_by_color[color] |= bit
        self._occupied |= bit
        self._zobrist_key ^= PIECE_KEYS[piece][square]

    def _remove_piece(self, piece: int, square: int) -> None:
        bit = BB_SQUARES[square]
        color = BLACK if piece > KING else WHITE
        self._squares[square] = NO_PIECE
        if piece == KING or piece == KING + 6:
            self._king_squares[color] = NO_SQUARE
        self._piece_bitboards[piece] ^= bit
        self._occupancy_by_color[color] ^= bit
        self._occupied ^= bit
        self._zobrist_key ^= PIECE_KEYS[piece][square]

    def _move_piece(self, piece: int, source: int, target: int) -> None:
        bits = BB_SQUARES[source] | BB_SQUARES[target]
        color = BLACK if piece > KING else WHITE
        self._squares[source] = NO_PIECE
        self._squares[target] = piece
        if piece == KING or piece == KING + 6:
            self._king_squares[color] = target
        self._piece_bitboards[piece] ^= bits
        self._occupancy_by_color[color] ^= bits
        self._occupied ^= bits
        self._zobrist_key ^= PIECE_KEYS[piece][source] ^ PIECE_KEYS[piece][target]

    def _ep_hash_file(self, ep_square: int, side_to_move: int) -> int:
        if ep_square == NO_SQUARE:
            return NO_SQUARE
        attackers = (
            PAWN_ATTACKS[side_to_move ^ 1][ep_square]
            & self._piece_bitboards[PAWN + side_to_move * 6]
        )
        return file_of(ep_square) if attackers else NO_SQUARE

    def is_capture(self, move: Move) -> bool:
        return move_is_capture(move) or self._captured_square(move) != NO_SQUARE

    def is_en_passant(self, move: Move) -> bool:  # noqa: PLR6301
        return is_en_passant(move)

    def gives_check(self, move: Move) -> bool:
        self.push(move)
        gives_check = self.is_check()
        self.pop()
        return gives_check

    def is_fifty_moves(self) -> bool:
        return self._halfmove_clock >= 100

    def is_repetition(self, count: int = 3) -> bool:
        return self._key_history.count(self._zobrist_key) >= count

    def is_checkmate(self) -> bool:
        return self.is_check() and not any(self.generate_legal_moves())

    def is_stalemate(self) -> bool:
        return not self.is_check() and not any(self.generate_legal_moves())

    def is_game_over(self) -> bool:
        return (
            self.is_checkmate()
            or self.is_stalemate()
            or self.is_fifty_moves()
            or self.is_repetition()
            or self.has_insufficient_material()
        )

    def has_insufficient_material(self) -> bool:
        pawns_rooks_queens = (
            self._piece_bitboards[piece_code(WHITE, PAWN)]
            | self._piece_bitboards[piece_code(BLACK, PAWN)]
            | self._piece_bitboards[piece_code(WHITE, ROOK)]
            | self._piece_bitboards[piece_code(BLACK, ROOK)]
            | self._piece_bitboards[piece_code(WHITE, QUEEN)]
            | self._piece_bitboards[piece_code(BLACK, QUEEN)]
        )
        if pawns_rooks_queens:
            return False

        knights = (
            self._piece_bitboards[piece_code(WHITE, KNIGHT)]
            | self._piece_bitboards[piece_code(BLACK, KNIGHT)]
        )
        bishops = (
            self._piece_bitboards[piece_code(WHITE, BISHOP)]
            | self._piece_bitboards[piece_code(BLACK, BISHOP)]
        )
        minor_count = popcount(knights | bishops)
        if minor_count <= 1:
            return True
        if knights:
            return False
        light_bishops = bishops & 0x55AA55AA55AA55AA
        dark_bishops = bishops & 0xAA55AA55AA55AA55
        return not light_bishops or not dark_bishops

    def perft(self, depth: int) -> int:
        if depth == 0:
            return 1
        if depth == 1:
            return len(self.generate_legal_moves())

        nodes = 0
        for move in self.generate_legal_moves():
            self.push(move)
            nodes += self.perft(depth - 1)
            self.pop()
        return nodes

    def perft_divide(self, depth: int) -> dict[str, int]:
        result: dict[str, int] = {}
        for move in self.generate_legal_moves():
            self.push(move)
            result[uci(move)] = self.perft(depth - 1)
            self.pop()
        return result

    def __str__(self) -> str:
        rows: list[str] = []
        for rank in range(7, -1, -1):
            row = []
            for file_index in range(8):
                piece = self._squares[rank * 8 + file_index]
                row.append("." if piece == NO_PIECE else piece_symbol(piece))
            rows.append(" ".join(row))
        return "\n".join(rows)

    def __repr__(self) -> str:
        return f"Board({self.fen()!r})"
