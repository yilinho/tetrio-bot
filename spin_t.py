"""Detect T-spin and mini T-spin placements."""

import numpy as np

from constants import NUM_COL

t_spin_triple_mask_2spin_left = np.array([
        [0, 1, 1],
        [0, 0, 1],
        [0, 1, 1],
        [0, 0, 0],
        [1, 0, 0]
    ], dtype=np.int32
)
t_spin_triple_mask_2spin_right = t_spin_triple_mask_2spin_left[::, ::-1]
stsd_dont_care_mask = np.array([
        [0, 1, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0],
        [0, 0, 0]
    ], dtype=np.int32
)


def get_t_slots(
        board, board_terrain, row_holes=None
) -> list[tuple[tuple[int, int], int, int, int, tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]]]:
    slots = []
    row_sum = board.sum(axis=1)
    if row_holes is None:
        row_holes = ((board == 0) & (np.cumsum(board, axis=0) < np.sum(board, axis=0))).sum(axis=1)

    if max(board_terrain) > 16:
        return []

    # t-spin double
    for x in range(NUM_COL - 2):
        # outer(base-level), center, inner(hole)
        center = x + 1
        for outer, inner, moves, move_x in (
            (x, x + 2, (3, 3), x),
            (x + 2, x, (1, 1), x + 1),
        ):
            if not board_terrain[center] < board_terrain[outer] < board_terrain[inner]:
                continue
            base_height = board_terrain[outer]
            if board[base_height][inner] == 0 and board[base_height - 1][inner] == 1 and board[base_height + 1][inner] == 1:
                actual_lines = int(row_sum[base_height] == 7) + int(row_sum[base_height - 1] == 9)
                slots.append((
                    moves, move_x, 2,  actual_lines,
                    ((base_height, outer), (base_height, center), (base_height, inner), (base_height - 1, center))
                ))

    # t-spin triple
    for x in range(NUM_COL - 2):
        for outer_wall, outer, center, inner, inner_wall, moves_single, move_x_single, moves, move_x in (
            (x + 3, x + 2, x + 1, x, x - 1, (0, 12, 3), x - 1, (1, 3, 3), x),
            (x - 1, x, x + 1, x + 2, x + 3, (0, 11, 1), x + 1, (3, 1, 1), x + 1),
        ):
            if board_terrain[outer] < 5:
                continue
            for y in range(5, board_terrain[outer] + 1):
                single_spin = False
                if board_terrain[center] != y-2 or board_terrain[inner] != y-2:
                    continue
                if 0 <= outer_wall < NUM_COL and not np.all(board[y-5:y-1, outer_wall]):
                    continue
                if y > 5 and board[y-6][center] == 0 and board[y-5][outer] == 0:
                    continue
                if not 0 <= inner_wall < NUM_COL or board[y-1][inner_wall] == 1 and board[y-2][inner_wall] == 1:
                    pass
                elif board_terrain[inner_wall] <= y-2:
                    single_spin = True
                else:
                    continue
                if outer < inner_wall:
                    masked = np.equal(board[y-5:y, outer:inner_wall], t_spin_triple_mask_2spin_left)
                else:
                    masked = np.equal(board[y-5:y, inner_wall+1:outer+1], t_spin_triple_mask_2spin_right)
                if np.all(masked | stsd_dont_care_mask):
                    actual_lines = int(row_sum[y-3] == 9) + int(row_sum[y-4] == 8) + int(row_sum[y-5] == 9)

                    if single_spin:
                        slots.append((
                            moves_single, move_x_single, 3, actual_lines,
                            ((y-3, outer), (y-4, outer), (y-5, outer), (y-4, center))
                        ))
                    else:
                        slots.append((
                            moves, move_x, 3, actual_lines,
                            ((y-3, outer), (y-4, outer), (y-5, outer), (y-4, center))
                        ))

    slots.sort(key=lambda a: (-a[3], a[2]))  # actual_lines desc -> expected_lines asc
    return slots


def get_mini_t_slots(board, board_terrain):
    slots = []
    row_sum = board.sum(axis=1)

    if max(board_terrain) > 17:
        return []

    # t-spin single (covered)
    for x in range(NUM_COL - 2):
        if not board_terrain[x] == board_terrain[x+1] < board_terrain[x+2]:
            continue
        if all((
            x == 0 or board[board_terrain[x]][x-3] == 1 and board[board_terrain[x]+1][x-1] == 1,  # at least 2 block higher
            board[board_terrain[x]][x + 2] == 0 and board[board_terrain[x] + 1][x + 2] == 1,
            board_terrain[x] == 0 or board[board_terrain[x] - 1][x + 2] == 1,
            row_sum[board_terrain[x]] == 7
        )):
            slots.append((
                (1, 3),  x, 1, 1, 1,
                ((board_terrain[x], x), (board_terrain[x], x + 1), (board_terrain[x], x + 2), (board_terrain[x] + 1, x + 1))
            ))
    for x in range(NUM_COL - 2):
        if not board_terrain[x+1] == board_terrain[x+2] < board_terrain[x]:
            continue
        if all((
            x + 3 == NUM_COL or board[board_terrain[x+2]][x+3] == 1 and board[board_terrain[x+2]+1][x+3] == 1,  # at least 2 block higher
            board[board_terrain[x+2]][x] == 0 and board[board_terrain[x+2] + 1][x] == 1,
            board_terrain[x+2] == 0 or board[board_terrain[x+2] - 1][x] == 1,
            row_sum[board_terrain[x+2]] == 7
        )):
            slots.append((
                (3, 1),  x+1, 1, 1, 1,
                ((board_terrain[x+2], x), (board_terrain[x+2], x + 1), (board_terrain[x+2], x + 2), (board_terrain[x+2] + 1, x + 1))
            ))

    # t-spin single (uncovered)
    for x in range(NUM_COL - 2):
        if not board_terrain[x + 1] == board_terrain[x + 2] > board_terrain[x]:
            continue
        if all((
            x == 0 or board[board_terrain[x + 2]][x - 1] == 1 and board[board_terrain[x + 2] + 1][x - 1] == 1,
            row_sum[board_terrain[x + 2] - 1] == 9
        )):
            slots.append((
                (0, 1), x, 1, 1, 1,
                ((board_terrain[x + 2], x + 1), (board_terrain[x + 2] - 1, x), (board_terrain[x + 2], x), (board_terrain[x + 2] + 1,  x))
            ))

    for x in range(NUM_COL - 2):
        if not board_terrain[x] == board_terrain[x + 1] > board_terrain[x+2]:
            continue
        if all((
            x + 3 == NUM_COL or board[board_terrain[x]][x + 3] == 1 and board[board_terrain[x] + 1][x + 3] == 1,
            row_sum[board_terrain[x] - 1] == 9
        )):
            slots.append((
                (0, 3), x, 1, 1, 1,
                ((board_terrain[x], x + 1), (board_terrain[x] - 1, x + 2), (board_terrain[x], x + 2), (board_terrain[x] + 1, x + 2))
            ))

    slots.sort(key=lambda a: (-a[4], a[3]))  # actual_lines desc -> expected_lines asc
    return slots
