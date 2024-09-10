import numpy as np

from constants import tetris_pieces_trimmed, NUM_ROW, NUM_COL
from spin_i import get_i_slots
from spin_jl import get_j_slots, get_l_slots
from spin_t import get_t_slots, get_mini_t_slots
from spin_zs import get_s_slots, get_z_slots

T_SPIN_MAX_HEIGHT = 10
TRIPLE_T_SPIN_MAX_HEIGHT = 8

ALL_SPIN_B2B = True


# belows are masks and constants to speedup calculation
range_1_20 = np.array(list(range(1, NUM_ROW + 1)))
full_board = np.zeros((NUM_ROW, NUM_COL), dtype=np.int32)
full_board.fill(1)
full_board_cumsum = full_board.cumsum(axis=0)
dead_board = np.zeros((NUM_ROW, NUM_COL), dtype=np.int32)
dead_board[:, 0] = 1


def find_best_move(current_board, current_piece, next_pieces, held_piece, combo, b2b, pruning_moves, pruning_breadth, mp_pool):
    all_moves = []

    # try to release T when there's t-slot, try to hold otherwise
    switch_extra = 0
    board_terrain = _get_board_terrain(current_board)
    t_slots = get_t_slots(current_board, board_terrain)
    if held_piece == "T":
        switch_extra -= 60
    if current_piece == "T":
        switch_extra += 60
    if len(t_slots) > 0 and t_slots[0][4] > 1:
        switch_extra = 0  # -switch_extra

    for new_score, position, rotations, extra_score, new_combo, new_b2b, new_board in _find_best_move(
        (current_board, current_piece, combo, b2b)
    ):
        all_moves.append([
            (position, rotations, False, new_combo, new_b2b, new_board),
            [(
                new_score, new_board, extra_score, new_combo, new_b2b, held_piece
            )]
        ])

    if held_piece != current_piece:  # no point to switch
        for new_score, position, rotations, extra_score, new_combo, new_b2b, new_board in _find_best_move(
            (current_board, held_piece, combo, b2b)
        ):
            all_moves.append([
                (position, rotations, True, new_combo, new_b2b, new_board),
                [(
                    new_score + switch_extra, new_board, extra_score, new_combo, new_b2b, current_piece
                )]
            ])

    all_moves.sort(reverse=True, key=lambda x: x[1][0][0])

    while next_pieces:
        current_piece, next_pieces = next_pieces[0], next_pieces[1:]
        next_results = []
        map_args = []
        for idx, _ in enumerate(all_moves):
            next_results.append([])
            for _, board, _, combo, b2b, held_piece in all_moves[idx][1]:
                map_args.append((board, current_piece, combo, b2b))
                if held_piece != current_piece:  # no point to switch
                    map_args.append((board, held_piece, combo, b2b))

        if mp_pool is None or len(map_args) < 10:
            map_res = map(_find_best_move, map_args)
        else:
            # print(len(map_args))
            map_res = iter(mp_pool.map(_find_best_move, map_args))

        for idx, _ in enumerate(all_moves):
            switch = all_moves[idx][0][2]
            for score, board, extra_score, combo, b2b, held_piece in all_moves[idx][1]:
                for new_score, _, _, new_extra_score, new_combo, new_b2b, new_board in next(map_res):
                    next_results[idx].append((
                        0.1 * score + 0.9 * (new_score + extra_score + (switch_extra if switch else 0)), new_board,
                        extra_score + new_extra_score, new_combo, new_b2b, held_piece
                    ))

                if held_piece != current_piece:  # no point to switch
                    for new_score, _, _, new_extra_score, new_combo, new_b2b, new_board in next(map_res):
                        next_results[idx].append((
                            0.1 * score + 0.9 * (new_score + extra_score + (switch_extra if switch else 0)), new_board,
                            extra_score + new_extra_score, new_combo, new_b2b, current_piece
                        ))

        for idx, _ in enumerate(all_moves):
            next_results[idx].sort(reverse=True, key=lambda x: x[0])
            if not next_results[idx]:
                all_moves[idx][1] = [(-99999, dead_board, 0, 0, 0, "Z")]
            else:
                all_moves[idx][1] = next_results[idx][:pruning_breadth]
        all_moves.sort(reverse=True, key=lambda x: x[1][0][0])
        all_moves = all_moves[:max(pruning_moves, len(all_moves) // 2)]

    if not all_moves:
        return -99999, (5, (0,), False, 0, 0, dead_board)
    best_move = all_moves[0]
    return best_move[1][0][0], best_move[0]


def get_all_possible_moves(piece, board, board_terrain, b2b):
    if piece == "T":  # t-spin moves
        for rot, pos, _, expected_lines, actual_lines, blocks in get_t_slots(board, board_terrain):
            new_board = board.copy()
            for y, x in blocks:
                new_board[y][x] = 1

            num_clear_rows = clear_full_rows(new_board)
            # assert num_clear_rows == actual_lines

            extra_score = 0
            if num_clear_rows > 0:
                if b2b:
                    if actual_lines == expected_lines:
                        extra_score += 300 + 100 * actual_lines * actual_lines
                    else:
                        extra_score += 100 + 40 * actual_lines
                else:
                    if actual_lines == expected_lines:
                        extra_score += 200 + 50 * actual_lines * actual_lines
                    else:
                        extra_score += 50 + 10 * actual_lines
                new_b2b = b2b + 1
            else:
                new_b2b = b2b
            yield pos, rot, extra_score, num_clear_rows, new_b2b, new_board

        for rot, pos, _, _, _, blocks in get_mini_t_slots(board, board_terrain):
            new_board = board.copy()
            for y, x in blocks:
                new_board[y][x] = 1

            num_clear_rows = clear_full_rows(new_board)

            extra_score = 0
            if num_clear_rows > 0:
                if b2b:
                    extra_score += 130 * num_clear_rows
                else:
                    extra_score += 70 * num_clear_rows
                new_b2b = b2b + 1
            else:
                new_b2b = b2b
            yield pos, rot, extra_score, num_clear_rows, new_b2b, new_board

    else:  # other spin moves. These moves don't give extra score but benefit to b2b counts.
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
                slots = []
        for rot, pos, blocks in slots:
            new_board = board.copy()
            for y, x in blocks:
                new_board[y][x] = 1

            num_clear_rows = clear_full_rows(new_board)

            extra_score = 0
            if num_clear_rows > 0:
                # extra_score += 3000
                if ALL_SPIN_B2B:
                    if b2b:
                        extra_score += 80 * num_clear_rows
                    else:
                        extra_score += 30 * num_clear_rows
                    new_b2b = b2b + 1
                else:
                    new_b2b = 0
            else:
                new_b2b = b2b
            yield pos, rot, extra_score, num_clear_rows, new_b2b, new_board

    for rotation, (piece_shape, piece_terrain) in enumerate(tetris_pieces_trimmed[piece]):
        positions = get_positions(board_terrain, piece_terrain)
        for position in positions:
            new_board = place_piece(board, piece_shape, position)
            if new_board is None:
                continue
            num_clear_rows = clear_full_rows(new_board)

            if num_clear_rows == 4:
                new_b2b = b2b + 1
            elif num_clear_rows > 0:
                new_b2b = 0
            else:
                new_b2b = b2b
            yield position[1], (rotation,), 0, num_clear_rows, new_b2b, new_board


def _find_best_move(args):
    current_board, current_piece, combo, b2b = args
    scores = []
    board_terrain = _get_board_terrain(current_board)

    for position, rotations, extra_score, num_clear_rows, new_b2b, new_board in get_all_possible_moves(current_piece, current_board, board_terrain, b2b):
        if num_clear_rows > 0:
            new_combo = combo + 1
        else:
            new_combo = 0
        score = evaluate_board(new_board)
        if score > 8000:  # perfect situation
            return (score, position, rotations, score, combo + 1, new_b2b, new_board),

        if num_clear_rows == 4:
            if b2b:
                return (score + 600, position, rotations, 600, combo + 1, new_b2b, new_board),
            return (score + 400, position, rotations, 400, combo + 1, new_b2b, new_board),
        if new_combo > 2:
            extra_score += 20
        if new_combo > 6:
            extra_score += 20
        if new_combo > 17:
            extra_score += 30

        if b2b > new_b2b:  # lost b2b
            extra_score -= 500
        scores.append((score + extra_score, position, rotations, extra_score, new_combo, new_b2b, new_board))
    return scores


def get_positions(board_terrain, piece_terrain):
    return [(max(board_terrain[x + i] - ht for i, ht in enumerate(piece_terrain)), x) for x in range(NUM_COL - len(piece_terrain) + 1)]


def place_piece(board, piece_shape, position):
    board = board.copy()
    try:
        board[position[0]:position[0] + piece_shape.shape[0], position[1]:position[1] + piece_shape.shape[1]] += piece_shape
    except ValueError:
        return None
    return board


def clear_full_rows(board):
    non_full_rows = np.not_equal(board.sum(axis=1), NUM_COL)
    r = NUM_ROW - int(non_full_rows.sum())
    if r > 0:
        # board = np.concatenate((board[non_full_rows], np.zeros((r, NUM_COL), dtype=np.int32)), axis=0)
        board[:NUM_ROW - r,] = board[non_full_rows]
        board[NUM_ROW - r:,] = 0
    return r


def _get_board_terrain(board):
    return [int((column * range_1_20).max()) for column in board.T]


def _has_i_slot(board, board_terrain):
    board_terrain_sorted = sorted(board_terrain)
    if board_terrain_sorted[0] + 4 > board_terrain_sorted[1]:
        return False, 0
    for x, h in enumerate(board_terrain):
        if h == board_terrain_sorted[0]:
            row_sum = board.sum(axis=1)
            return (row_sum[h] == 9 and row_sum[h+1] == 9 and row_sum[h+2] == 9 and row_sum[h+3] == 9), x
    return False, 0


def evaluate_board(board):
    score = 0

    board_terrain = _get_board_terrain(board)
    board_terrain_sorted = sorted(board_terrain)

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

    score -= 20 * i_slot_count * i_slot_count  # prevent multiple i slot
    score -= 50 * i_slot_count_too_high
    score -= 50 * tower_count

    # The number of holes - find number of 0s with 1s above
    row_holes = ((board == 0) & (np.cumsum(board, axis=0) < np.sum(board, axis=0))).sum(axis=1)
    score -= 60 * np.sum(row_holes)

    # The number of blockades - find number of 1s above holes
    blockades = np.sum(board & (np.cumsum(board, axis=0) < full_board_cumsum))
    score -= 25 * blockades

    if board_terrain_sorted[-1] == 0:  # prefect clear
        print("Prefect clear !!")
        return 9999

    if board_terrain_sorted[-1] >= 7:
        score -= board_terrain_sorted[-1]
    if board_terrain_sorted[-1] >= 12:
        score -= 2 * board_terrain_sorted[-1]
    if board_terrain_sorted[-1] >= 14:
        score -= 5 * board_terrain_sorted[-1]
    if board_terrain_sorted[-1] >= 16:
        score -= 5 * board_terrain_sorted[-1] * board_terrain_sorted[-1]

    score -= 10 * (board_terrain_sorted[-1] - board_terrain_sorted[1])  # second lowest
    diff_for_highest_2 = board_terrain_sorted[-1] - board_terrain_sorted[-2]
    score -= 10 * diff_for_highest_2 * diff_for_highest_2 * (diff_for_highest_2 - 1)  # make sure no single high column

    # try to make every column lower
    for h in board_terrain_sorted:
        if h > 12:
            score -= 5 * h * h
        elif h > 6:
            score -= 2 * h * (h - 5)
        else:
            score -= h

    # t slots logic below
    t_slots = get_t_slots(board, board_terrain, row_holes=row_holes)
    triple_count = 0
    for _, pos, max_lines, expected_lines, actual_lines, _ in t_slots:
        if max_lines == 3 and board_terrain_sorted[-1] < TRIPLE_T_SPIN_MAX_HEIGHT:
            triple_count += 1
            score += 300 + actual_lines * 100
        score += 80 * actual_lines - 50 * (max_lines - expected_lines)
    if triple_count > 1:
        score -= 500 * triple_count
    if max(board_terrain) < T_SPIN_MAX_HEIGHT and len(t_slots) == 1:  # try to make t-spin from scratch
        score += 40 * t_slots[0][3]

    return score
