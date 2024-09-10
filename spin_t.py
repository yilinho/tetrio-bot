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


def get_t_slots(board, board_terrain, row_holes=None):
    slots = []
    row_sum = board.sum(axis=1)
    if row_holes is None:
        row_holes = ((board == 0) & (np.cumsum(board, axis=0) < np.sum(board, axis=0))).sum(axis=1)

    if max(board_terrain) > 17:
        return []
    # t-spin double
    for x in range(NUM_COL - 2):
        if not board_terrain[x+1] < board_terrain[x] < board_terrain[x+2]:
            continue
        if board[board_terrain[x]][x+2] == 0 and board[board_terrain[x]-1][x+2] == 1 and board[board_terrain[x]+1][x+2] == 1:
            expected_lines = 2
            actual_lines = 0
            if row_sum[board_terrain[x]] == 7:
                actual_lines += 1
            elif row_holes[board_terrain[x]] > 1:
                expected_lines -= 1
            if row_sum[board_terrain[x]-1] == 9:
                actual_lines += 1
            elif row_holes[board_terrain[x]-1] > 0:
                expected_lines -= 1
            slots.append((
                (3, 3), x, 2, expected_lines, actual_lines,
                ((board_terrain[x], x), (board_terrain[x], x + 1), (board_terrain[x], x + 2), (board_terrain[x] - 1, x + 1))
            ))

    for x in range(NUM_COL - 2):
        if not board_terrain[x+1] < board_terrain[x+2] < board_terrain[x]:
            continue
        if board[board_terrain[x+2]][x] == 0 and board[board_terrain[x+2]-1][x] == 1 and board[board_terrain[x+2]+1][x] == 1:
            expected_lines = 2
            actual_lines = 0
            if row_sum[board_terrain[x+2]] == 7:
                actual_lines += 1
            elif row_holes[board_terrain[x+2]] > 1:
                expected_lines -= 1
            if row_sum[board_terrain[x+2]-1] == 9:
                actual_lines += 1
            elif row_holes[board_terrain[x+2]-1] > 0:
                expected_lines -= 1
            slots.append((
                (1, 1), x + 1, 2, expected_lines, actual_lines,
                ((board_terrain[x+2], x), (board_terrain[x+2], x + 1), (board_terrain[x+2], x + 2), (board_terrain[x+2] - 1, x + 1))
            ))

    # t-spin triple
    for x in range(NUM_COL - 3):
        if board_terrain[x] < 5:
            continue
        for y in range(5, board_terrain[x] + 1):
            single_spin = False
            if board_terrain[x+1] != y-2 or board_terrain[x+2] != y-2:
                continue
            if x > 0 and not np.all(board[y-5:y-1, x-1]):
                continue
            if y > 5 and board[y-6][x+1] == 0 and board[y-5][x] == 0:
                continue
            if x + 3 == NUM_COL or board[y-1][x+3] == 1 and board[y-2][x+3] == 1:
                pass
            elif board_terrain[x+3] <= y-2:
                single_spin = True
            else:
                continue
            if np.all(np.equal(board[y-5:y, x:x+3], t_spin_triple_mask_2spin_left) | stsd_dont_care_mask):
                expected_lines = 3
                actual_lines = 0
                if row_sum[y-3] == 9:
                    actual_lines += 1
                elif row_holes[y-3] > 1:
                    expected_lines -= 1
                if row_sum[y-4] == 8:
                    actual_lines += 1
                elif row_holes[y-4] > 2:
                    expected_lines -= 1
                if row_sum[y-5] == 9:
                    actual_lines += 1
                elif row_holes[y-5] > 1:
                    expected_lines -= 1

                if single_spin:
                    slots.append((
                        (0, 11, 1), x + 1, 3, expected_lines, actual_lines,
                        ((y-3, x), (y-4, x), (y-5, x), (y-4, x + 1))
                    ))
                else:
                    slots.append((
                        (3, 1, 1), x + 1, 3, expected_lines, actual_lines,
                        ((y-3, x), (y-4, x), (y-5, x), (y-4, x + 1))
                    ))

    for x in range(NUM_COL - 3):
        if board_terrain[x+2] < 5:
            continue
        for y in range(5, board_terrain[x] + 1):

            single_spin = False
            if board_terrain[x] != y-2 or board_terrain[x+1] != y-2:
                continue
            if x+2 < NUM_COL - 1 and not np.all(board[y-5:y-1, x+3]):
                continue

            if y > 5 and board[y-6][x+2] == 0 and board[y-5][x+1] == 0:
                continue
            if x == 0 or board[y-1][x-1] == 1 and board[y-2][x-1] == 1:
                pass
            elif board_terrain[x-1] <= y-2:
                single_spin = True
            else:
                continue
            if np.all(np.equal(board[y-5:y, x:x+3], t_spin_triple_mask_2spin_right) | stsd_dont_care_mask):
                expected_lines = 3
                actual_lines = 0
                if row_sum[y-3] == 9:
                    actual_lines += 1
                elif row_holes[y-3] > 1:
                    expected_lines -= 1
                if row_sum[y-4] == 8:
                    actual_lines += 1
                elif row_holes[y-4] > 2:
                    expected_lines -= 1
                if row_sum[y-5] == 9:
                    actual_lines += 1
                elif row_holes[y-5] > 1:
                    expected_lines -= 1

                if single_spin:
                    slots.append((
                        (0, 12, 3), x-1, 3, expected_lines, actual_lines,
                        ((y - 3, x + 2), (y - 4, x + 2), (y - 5, x + 2), (y - 4, x + 1))
                    ))
                else:
                    slots.append((
                        (1, 3, 3), x, 3, expected_lines, actual_lines,
                        ((y - 3, x + 2), (y - 4, x + 2), (y - 5, x + 2), (y - 4, x + 1))
                    ))

    slots.sort(key=lambda a: (-a[4], a[3]))  # actual_lines desc -> expected_lines asc
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
