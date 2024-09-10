from constants import NUM_COL


def get_i_slots(board, board_terrain):
    slots = []

    if max(board_terrain) > 14:
        return []

    for x in range(NUM_COL - 3):
        if not board_terrain[x] + 1 < max(board_terrain[x + 1], board_terrain[x + 2], board_terrain[x + 3]):
            continue
        if all((
            x == 0 or board[board_terrain[x]][x-1] == 1 and board[board_terrain[x]+1][x-1] == 1 and board[board_terrain[x]+2][x-1] == 1 and board[board_terrain[x]+3][x-1] == 1,
            x + 4 == NUM_COL or board[board_terrain[x]][x+4] == 1,
            board[board_terrain[x]][x+1] == 0 and board[board_terrain[x]][x+2] == 0 and board[board_terrain[x]][x+3] == 0,
            board[board_terrain[x] + 1][x+1] == 1 or board[board_terrain[x] + 1][x+2] == 1 or board[board_terrain[x] + 1][x+3] == 1,
        )):
            slots.append((
                (1, 1), x,
                ((board_terrain[x], x), (board_terrain[x], x + 1), (board_terrain[x], x + 2), (board_terrain[x], x + 3))
            ))
    for x in range(NUM_COL - 3):
        if not board_terrain[x + 3] + 1 < max(board_terrain[x], board_terrain[x + 1], board_terrain[x + 2]):
            continue
        if all((
            x == 0 or board[board_terrain[x+3]][x-1] == 1,
            x + 4 == NUM_COL or board[board_terrain[x+3]][x+4] == 1 and board[board_terrain[x+3]+1][x+4] == 1 and board[board_terrain[x+3]+2][x+4] == 1 and board[board_terrain[x+3]+3][x+4] == 1,
            board[board_terrain[x+3]][x] == 0 and board[board_terrain[x+3]][x+1] == 0 and board[board_terrain[x+3]][x+2] == 0,
            board[board_terrain[x+3] + 1][x] == 1 or board[board_terrain[x+3] + 1][x+1] == 1 or board[board_terrain[x+3] + 1][x+2] == 1,
        )):
            slots.append((
                (3, 3), x + 4,
                ((board_terrain[x+3], x), (board_terrain[x+3], x + 1), (board_terrain[x+3], x + 2), (board_terrain[x+3], x + 3))
            ))
    return slots
