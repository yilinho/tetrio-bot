"""Search and evaluate candidate TETR.IO moves."""

from collections.abc import Iterable, Iterator, Sequence
from multiprocessing.pool import Pool
from typing import Any, TypeAlias

import numpy as np
from numpy.typing import NDArray

import weights
from constants import NUM_COL, NUM_ROW, tetris_pieces_trimmed
from spin_i import get_i_slots
from spin_jl import get_j_slots, get_l_slots
from spin_t import get_mini_t_slots, get_t_slots
from spin_zs import get_s_slots, get_z_slots
from type_defs import Board, Coordinate, Rotation, SpinSlot

MoveCandidate: TypeAlias = tuple[float, int, Rotation, float, int, int, Board]
PlacedMove: TypeAlias = tuple[int, Rotation, int, int, int, Board]
FutureState: TypeAlias = tuple[float, Board, float, int, int, str]

T_SPIN_MAX_HEIGHT = 10
TRIPLE_T_SPIN_MAX_HEIGHT = 8

# belows are masks and constants to speedup calculation
range_1_20 = np.array(list(range(1, NUM_ROW + 1)))
full_board = np.zeros((NUM_ROW, NUM_COL), dtype=np.int32)
full_board.fill(1)
full_board_cumsum = full_board.cumsum(axis=0)
dead_board = np.zeros((NUM_ROW, NUM_COL), dtype=np.int32)
dead_board[:, 0] = 1


def find_best_move(
    current_board: Board,
    current_piece: str,
    next_pieces: Sequence[str],
    held_piece: str,
    combo: int,
    b2b: int,
    pruning_moves: int,
    pruning_breadth: int,
    mp_pool: Pool | None,
) -> tuple[float, tuple[int, Rotation, bool, int, int, Board]]:
    all_moves: list[
        tuple[
            tuple[int, Rotation, bool, int, int, Board],
            list[tuple[float, Board, float, int, int, str]],
        ]
    ] = []

    # Calculate the first-move Hold preference.
    # Try to release T when there's t-slot, hold it otherwise
    # It is carried through lookahead to preserve its full score weight.
    if held_piece != current_piece and (held_piece == "T" or current_piece == "T"):
        board_terrain = _get_board_terrain(current_board)
        t_slots = get_t_slots(current_board, board_terrain)
        if len(t_slots) > 0 and t_slots[0][3] > 1:  # t_slots is sorted
            switch_extra = 0
        elif held_piece == "T":
            switch_extra = -weights.HOLD_T_PREFERENCE
        else:
            switch_extra = weights.HOLD_T_PREFERENCE
    else:
        switch_extra = 0

    for new_score, position, rotations, extra_score, new_combo, new_b2b, new_board in _find_best_move(
        (current_board, current_piece, combo, b2b)
    ):
        all_moves.append((
            (position, rotations, False, new_combo, new_b2b, new_board),
            [(
                new_score, new_board, extra_score, new_combo, new_b2b, held_piece
            )]
        ))

    if held_piece != current_piece:  # no point to switch
        for new_score, position, rotations, extra_score, new_combo, new_b2b, new_board in _find_best_move(
            (current_board, held_piece, combo, b2b)
        ):
            all_moves.append((
                (position, rotations, True, new_combo, new_b2b, new_board),
                [(
                    new_score + switch_extra, new_board, extra_score, new_combo, new_b2b, current_piece
                )]
            ))

    all_moves.sort(reverse=True, key=lambda x: x[1][0][0])

    while next_pieces:
        current_piece, next_pieces = next_pieces[0], next_pieces[1:]
        next_results: list[list[FutureState]] = []
        map_args = []
        for idx, _ in enumerate(all_moves):
            next_results.append([])
            for _, _board, _, _combo, _b2b, _held_piece in all_moves[idx][1]:
                map_args.append((_board, current_piece, _combo, _b2b))
                if _held_piece != current_piece:  # no point to switch
                    map_args.append((_board, _held_piece, _combo, _b2b))

        if mp_pool is None or len(map_args) < 10:
            map_res: Iterator[Iterable[MoveCandidate]] = map(_find_best_move, map_args)
        else:
            # print(len(map_args))
            map_res = iter(mp_pool.map(_find_best_move, map_args))

        for idx, _ in enumerate(all_moves):
            switch = all_moves[idx][0][2]
            for _score, _, _extra_score, _, _, _held_piece in all_moves[idx][1]:
                for new_score, _, _, new_extra_score, new_combo, new_b2b, new_board in next(map_res):
                    next_results[idx].append((
                        weights.CURRENT_MOVE_WEIGHT * _score + weights.LOOKAHEAD_WEIGHT * (new_score + _extra_score + (switch_extra if switch else 0)), new_board,
                        _extra_score + new_extra_score, new_combo, new_b2b, _held_piece
                    ))

                if _held_piece != current_piece:  # no point to switch
                    for new_score, _, _, new_extra_score, new_combo, new_b2b, new_board in next(map_res):
                        next_results[idx].append((
                            weights.CURRENT_MOVE_WEIGHT * _score + weights.LOOKAHEAD_WEIGHT * (new_score + _extra_score + (switch_extra if switch else 0)), new_board,
                            _extra_score + new_extra_score, new_combo, new_b2b, current_piece
                        ))

        for idx, _ in enumerate(all_moves):
            next_results[idx].sort(reverse=True, key=lambda x: x[0])
            if not next_results[idx]:
                all_moves[idx] = (all_moves[idx][0], [(weights.DEAD_MOVE_SCORE, dead_board, 0, 0, 0, "Z")])
            else:
                all_moves[idx] = (all_moves[idx][0], next_results[idx][:pruning_breadth])
        all_moves.sort(reverse=True, key=lambda x: x[1][0][0])
        all_moves = all_moves[:max(pruning_moves, len(all_moves) // 2)]

    if not all_moves:
        return weights.DEAD_MOVE_SCORE, (5, (0,), False, 0, 0, dead_board)
    best_move = all_moves[0]
    return best_move[1][0][0], best_move[0]


def get_all_possible_moves(
    piece: str,
    board: Board,
    board_terrain: list[int],
    b2b: int,
) -> Iterable[PlacedMove]:
    if piece == "T":  # t-spin moves
        for rot, pos, expected_lines, actual_lines, blocks in get_t_slots(board, board_terrain):
            new_board = board.copy()
            for y, x in blocks:
                new_board[y][x] = 1

            num_clear_rows = clear_full_rows(new_board)
            # assert num_clear_rows == actual_lines

            extra_score = 0
            if num_clear_rows > 0:
                if b2b:
                    if actual_lines == expected_lines:
                        extra_score += weights.T_SPIN_B2B_BASE + weights.T_SPIN_B2B_LINE_WEIGHT * actual_lines * actual_lines
                    else:
                        extra_score += weights.T_SPIN_B2B_INCOMPLETE_BASE + weights.T_SPIN_B2B_INCOMPLETE_LINE_WEIGHT * actual_lines
                else:
                    if actual_lines == expected_lines:
                        extra_score += weights.T_SPIN_NORMAL_BASE + weights.T_SPIN_NORMAL_LINE_WEIGHT * actual_lines * actual_lines
                    else:
                        extra_score += weights.T_SPIN_INCOMPLETE_BASE + weights.T_SPIN_INCOMPLETE_LINE_WEIGHT * actual_lines
                new_b2b = b2b + 1
            else:
                new_b2b = b2b
            yield pos, rot, extra_score, num_clear_rows, new_b2b, new_board

        for rot, pos, _, _, blocks in get_mini_t_slots(board, board_terrain):
            new_board = board.copy()
            for y, x in blocks:
                new_board[y][x] = 1

            num_clear_rows = clear_full_rows(new_board)

            extra_score = 0
            if num_clear_rows > 0:
                if b2b:
                    extra_score += weights.MINI_T_SPIN_B2B_LINE_WEIGHT * num_clear_rows
                else:
                    extra_score += weights.MINI_T_SPIN_LINE_WEIGHT * num_clear_rows
                new_b2b = b2b + 1
            else:
                new_b2b = b2b
            yield pos, rot, extra_score, num_clear_rows, new_b2b, new_board

    else:  # other spin moves. These moves don't give extra score but benefit to b2b counts.
        slots: list[SpinSlot] = []
        match piece:
            case "S":
                slots = get_s_slots(board, board_terrain)
            case "Z":
                slots = get_z_slots(board, board_terrain)
            case "I":
                slots = get_i_slots(board, board_terrain)
            case "L":
                slots = get_l_slots(board, board_terrain)
            case "J":
                slots = get_j_slots(board, board_terrain)
            case _:
                pass
        for rot, pos, blocks in slots:
            new_board = board.copy()
            for y, x in blocks:
                new_board[y][x] = 1

            num_clear_rows = clear_full_rows(new_board)

            extra_score = 0
            if num_clear_rows > 0:
                if weights.ALL_SPIN_B2B:
                    if b2b:
                        extra_score += weights.ALL_SPIN_B2B_LINE_WEIGHT * num_clear_rows
                    else:
                        extra_score += weights.ALL_SPIN_NORMAL_LINE_WEIGHT * num_clear_rows
                    new_b2b = b2b + 1
                else:
                    new_b2b = 0
            else:
                new_b2b = b2b
            yield pos, rot, extra_score, num_clear_rows, new_b2b, new_board

    for rotation, (piece_shape, piece_terrain) in enumerate(tetris_pieces_trimmed[piece]):
        positions = get_positions(board_terrain, piece_terrain)
        for position in positions:
            placed_board = place_piece(board, piece_shape, position)
            if placed_board is None:
                continue
            num_clear_rows = clear_full_rows(placed_board)

            if num_clear_rows == 4:
                new_b2b = b2b + 1
            elif num_clear_rows > 0:
                new_b2b = 0
            else:
                new_b2b = b2b
            yield position[1], (rotation,), 0, num_clear_rows, new_b2b, placed_board


def _find_best_move(args: tuple[Board, str, int, int]) -> Iterable[MoveCandidate]:
    current_board, current_piece, combo, b2b = args
    scores = []
    board_terrain = _get_board_terrain(current_board)

    for position, rotations, extra_score, num_clear_rows, new_b2b, new_board in get_all_possible_moves(current_piece, current_board, board_terrain, b2b):
        if num_clear_rows > 0:
            new_combo = combo + 1
        else:
            new_combo = 0
        score = evaluate_board(new_board)
        if score > weights.PERFECT_SITUATION_THRESHOLD:
            return (score, position, rotations, score, combo + 1, new_b2b, new_board),

        if num_clear_rows == 4:
            if b2b:
                return (score + weights.TETRIS_B2B_BONUS, position, rotations, weights.TETRIS_B2B_BONUS, combo + 1, new_b2b, new_board),
            return (score + weights.TETRIS_NORMAL_BONUS, position, rotations, weights.TETRIS_NORMAL_BONUS, combo + 1, new_b2b, new_board),
        for combo_threshold, combo_bonus in weights.COMBO_BONUS_THRESHOLDS:
            if new_combo > combo_threshold:
                extra_score += combo_bonus

        if b2b > new_b2b:  # lost b2b
            extra_score += weights.B2B_LOSS_PENALTY
        scores.append((score + extra_score, position, rotations, extra_score, new_combo, new_b2b, new_board))
    return scores


def get_positions(board_terrain: list[int], piece_terrain: Sequence[int] | NDArray[np.integer[Any]]) -> list[Coordinate]:
    return [(max(board_terrain[x + i] - ht for i, ht in enumerate(piece_terrain)), x) for x in range(NUM_COL - len(piece_terrain) + 1)]


def place_piece(board: Board, piece_shape: Board, position: Coordinate) -> Board | None:
    board = board.copy()
    try:
        board[position[0]:position[0] + piece_shape.shape[0], position[1]:position[1] + piece_shape.shape[1]] += piece_shape
    except ValueError:
        return None
    return board


def clear_full_rows(board: Board) -> int:
    non_full_rows = np.not_equal(board.sum(axis=1), NUM_COL)
    r = NUM_ROW - int(non_full_rows.sum())
    if r > 0:
        # board = np.concatenate((board[non_full_rows], np.zeros((r, NUM_COL), dtype=np.int32)), axis=0)
        board[:NUM_ROW - r,] = board[non_full_rows]
        board[NUM_ROW - r:,] = 0
    return r


def _get_board_terrain(board: Board) -> list[int]:
    return [int((column * range_1_20).max()) for column in board.T]


def evaluate_board(board: Board) -> float:
    score = 0

    board_terrain = _get_board_terrain(board)

    i_slot_count = 0
    if board_terrain[0] + 2 < board_terrain[1]:
        i_slot_count += 1
    if board_terrain[-1] + 2 < board_terrain[-2]:
        i_slot_count += 1
    for i in range(1, NUM_COL - 1):
        if board_terrain[i] + 2 < board_terrain[i-1] and board_terrain[i] + 2 < board_terrain[i+1]:
            i_slot_count += 1
    i_slot_count_too_high = 0
    if board_terrain[0] + 5 < board_terrain[1]:
        i_slot_count_too_high += 1
    if board_terrain[-1] + 5 < board_terrain[-2]:
        i_slot_count_too_high += 1
    for i in range(1, NUM_COL - 1):
        if board_terrain[i] + 5 < board_terrain[i-1] and board_terrain[i] + 5 < board_terrain[i+1]:
            i_slot_count_too_high += 1

    tower_count = 0
    for i in range(1, NUM_COL - 1):
        if board_terrain[i] > board_terrain[i-1] + 2 and board_terrain[i] > board_terrain[i+1] + 2:
            tower_count += 1

    score += weights.I_SLOT_PENALTY * (i_slot_count ** 3)  # prevent multiple i slot
    score += weights.HIGH_I_SLOT_PENALTY * i_slot_count_too_high
    score += weights.TOWER_PENALTY * tower_count

    # The number of holes - find number of 0s with 1s above
    row_holes = ((board == 0) & (np.cumsum(board, axis=0) < np.sum(board, axis=0))).sum(axis=1)
    score += weights.HOLE_PENALTY * (np.sum(row_holes) ** 1.3)

    # The number of blockades - find number of 1s above holes
    blockades = np.sum(board & (np.cumsum(board, axis=0) < full_board_cumsum))
    score += weights.BLOCKADE_PENALTY * blockades

    board_terrain_sorted = sorted(board_terrain)
    current_max_height = board_terrain_sorted[-1]
    if current_max_height == 0:  # perfect clear
        print("Perfect clear !!")
        return weights.PERFECT_CLEAR_SCORE

    for _threshold, _linear_weight, _quadratic_weight in weights.HEIGHT_PENALTIES:
        if current_max_height >= _threshold:
            score += _linear_weight * current_max_height
            score += _quadratic_weight * current_max_height * current_max_height

    score += weights.SECOND_LOWEST_HEIGHT_PENALTY * (current_max_height - board_terrain_sorted[1])  # second lowest because of i-slot
    diff_for_highest_2 = current_max_height - board_terrain_sorted[-2]
    score += weights.ISOLATED_HIGH_COLUMN_PENALTY * diff_for_highest_2 * diff_for_highest_2 * (diff_for_highest_2 - 1)  # make sure no single high column

    # try to make every column lower
    for h in board_terrain_sorted:
        for _threshold, _linear_weight, _quadratic_weight in weights.COLUMN_HEIGHT_PENALTIES:
            if h >= _threshold:
                score += _linear_weight * h
                score += _quadratic_weight * h * h
                break

    # t slots logic below
    t_slots = get_t_slots(board, board_terrain)
    triple_count = 0
    for _, _, expected_lines, actual_lines, _ in t_slots:
        if expected_lines == 3:
            triple_count += 1
            if current_max_height < TRIPLE_T_SPIN_MAX_HEIGHT:
                score += weights.TRIPLE_T_SPIN_REWARD + actual_lines * weights.TRIPLE_T_SPIN_LINE_WEIGHT
        score += weights.T_SLOT_LINE_WEIGHT * actual_lines + weights.T_SLOT_EXPECTED_LINE_PENALTY * (expected_lines - actual_lines)
    if triple_count > 1:
        score += weights.MULTIPLE_TRIPLE_T_SPIN_PENALTY * triple_count
    if current_max_height < T_SPIN_MAX_HEIGHT and len(t_slots) == 1:  # try to make t-spin from scratch
        score += weights.LOW_BOARD_T_SLOT_REWARD * t_slots[0][2]

    return score
