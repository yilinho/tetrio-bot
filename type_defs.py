"""Shared type aliases used by the AI and spin detection modules."""

from typing import TypeAlias

import numpy as np
from numpy.typing import NDArray

Board: TypeAlias = NDArray[np.int32]
Coordinate: TypeAlias = tuple[int, int]
Rotation: TypeAlias = tuple[int, ...]

SpinSlotT: TypeAlias = tuple[Rotation, int, int, int, tuple[Coordinate, Coordinate, Coordinate, Coordinate]]
SpinSlot: TypeAlias = tuple[Rotation, int, tuple[Coordinate, Coordinate, Coordinate, Coordinate]]
