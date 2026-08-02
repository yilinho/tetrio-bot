"""Centralized AI scoring weights.

Only values that affect the AI's preference between moves belong here.
Geometry and search limits remain in their respective modules/configuration.
"""

# Lookahead aggregation
CURRENT_MOVE_WEIGHT = 0.1
LOOKAHEAD_WEIGHT = 0.9

# Hold preference for T pieces
HOLD_T_PREFERENCE = 60

# T-spin scoring
T_SPIN_B2B_BASE = 300
T_SPIN_B2B_LINE_WEIGHT = 100
T_SPIN_NORMAL_BASE = 200
T_SPIN_NORMAL_LINE_WEIGHT = 50
T_SPIN_B2B_INCOMPLETE_BASE = 100
T_SPIN_B2B_INCOMPLETE_LINE_WEIGHT = 40
T_SPIN_INCOMPLETE_BASE = 50
T_SPIN_INCOMPLETE_LINE_WEIGHT = 10

# Mini T-spin scoring
MINI_T_SPIN_B2B_LINE_WEIGHT = 130
MINI_T_SPIN_LINE_WEIGHT = 70

# Other spin scoring
ALL_SPIN_B2B = True
ALL_SPIN_B2B_LINE_WEIGHT = 80
ALL_SPIN_NORMAL_LINE_WEIGHT = 30

# Line clear and combo scoring
TETRIS_B2B_BONUS = 600
TETRIS_NORMAL_BONUS = 400
COMBO_BONUS_THRESHOLDS = (
    (2, 20),
    (6, 20),
    (17, 30),
)
B2B_LOSS_PENALTY = -500

# Board feature penalties
I_SLOT_PENALTY = -20
HIGH_I_SLOT_PENALTY = -50
TOWER_PENALTY = -50
HOLE_PENALTY = -60
BLOCKADE_PENALTY = -25
SECOND_LOWEST_HEIGHT_PENALTY = -10
ISOLATED_HIGH_COLUMN_PENALTY = -10

# Height penalties: (minimum height, linear weight, quadratic weight).
HEIGHT_PENALTIES = (
    (7, -1, 0),
    (12, -2, 0),
    (14, -5, 0),
    (16, 0, -5),
)
COLUMN_HEIGHT_PENALTIES = (
    (12, -5, -5),
    (6, -2, -0),
    (0, -1, -0),
)

# T-slot board-shaping rewards/penalties
TRIPLE_T_SPIN_REWARD = 300
TRIPLE_T_SPIN_LINE_WEIGHT = 100
T_SLOT_LINE_WEIGHT = 80
T_SLOT_EXPECTED_LINE_PENALTY = 50
MULTIPLE_TRIPLE_T_SPIN_PENALTY = -500
LOW_BOARD_T_SLOT_REWARD = 50

PERFECT_CLEAR_SCORE = 9999
PERFECT_SITUATION_THRESHOLD = 8000
DEAD_MOVE_SCORE = -99999
