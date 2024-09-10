import numpy as np

NUM_COL = 10
NUM_ROW = 20

# Colors for tetrio
colors = [
    (194, 64, 70),  # red - Z
    (142, 191, 61),  # lime - S
    (93, 76, 176),  # dark blue - J
    (192, 168, 64),  # yellow - O
    (62, 191, 144),  # turquoise - I
    (194, 115, 68),  # orange - L
    (176, 75, 166),  # purple - T
]
colors_name = "ZSJOILT"

tetris_pieces = {
    'I': [
        np.array([[1, 1, 1, 1]]),
        np.array([[0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 1, 0], [0, 0, 1, 0]])
    ],
    'O': [
        np.array([[0, 1, 1, 0], [0, 1, 1, 0]])
    ],
    'T': [
        np.array([[1, 1, 1, 0], [0, 1, 0, 0]]),
        np.array([[0, 1, 0, 0], [0, 1, 1, 0], [0, 1, 0, 0]]),
        np.array([[0, 1, 0, 0], [1, 1, 1, 0]]),
        np.array([[0, 1, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0]]),
    ],
    'L': [
        np.array([[1, 1, 1, 0], [0, 0, 1, 0]]),
        np.array([[0, 1, 1, 0], [0, 1, 0, 0], [0, 1, 0, 0]]),
        np.array([[1, 0, 0, 0], [1, 1, 1, 0]]),
        np.array([[0, 1, 0, 0], [0, 1, 0, 0], [1, 1, 0, 0]]),
    ],
    'J': [
        np.array([[1, 1, 1, 0], [1, 0, 0, 0]]),
        np.array([[0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0]]),
        np.array([[0, 0, 1, 0], [1, 1, 1, 0]]),
        np.array([[1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0]]),
    ],
    'Z': [
        np.array([[0, 1, 1, 0], [1, 1, 0, 0]]),
        np.array([[0, 1, 0, 0], [0, 1, 1, 0], [0, 0, 1, 0]])
    ],
    'S': [
        np.array([[1, 1, 0, 0], [0, 1, 1, 0]]),
        np.array([[0, 0, 1, 0], [0, 1, 1, 0], [0, 1, 0, 0]])
    ]
}

tetris_pieces_trimmed = {}
for k, shapes in tetris_pieces.items():
    tetris_pieces_trimmed[k] = []
    for piece_shape in shapes:
        piece_shape = piece_shape[~np.all(piece_shape == 0, axis=1)]
        piece_shape = piece_shape[:, ~np.all(piece_shape == 0, axis=0)]
        tetris_pieces_trimmed[k].append((piece_shape, piece_shape.argmax(axis=0)))
