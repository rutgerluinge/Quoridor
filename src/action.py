from dataclasses import dataclass
from typing import List, Optional, Tuple

from config import Config, Pos


class ActionSpace:
    s = Config()
    player_movement = {"up": (-1, 0), "right": (0, 1), "left": (0, -1), "down": (1, 0)}
    blocked_movement_idx_start = len(player_movement) - 1
    blocked_movement = {
        "jump_up": (-2, 0),
        "jump_down": (2, 0),
        "jump_left": (0, -2),
        "jump_right": (0, 2),
        "up_left": (-1, -1),
        "up_right": (-1, 1),
        "down_left": (1, -1),
        "down_right": (1, 1),
    }

    wall_vertical_idx_start = blocked_movement_idx_start + len(blocked_movement)
    wall_vertical_space = (s.N - 1) * (s.N + 1)

    wall_horizontal_idx_start = wall_vertical_idx_start + wall_vertical_space
    wall_horizontal_space = (s.N - 1) * (s.N + 1)

    action_space = (
        len(player_movement)
        + len(blocked_movement)
        + wall_vertical_space
        + wall_horizontal_space
    )


@dataclass
class Action:
    name: str
    idx: int


@dataclass
class PlayerAction(Action):
    dx: int
    dy: int


@dataclass
class BlockedPlayerAction(Action):
    dx: int
    dy: int


@dataclass
class WallAction(Action):
    edge1: Pos
    edge2: Pos

    def __post_init__(self):
        # Automatically set the name based on the wall’s unique string ID
        self.name = self.get_move_name()

    def get_move_name(self) -> str:
        """Return string rep"""
        e1 = tuple(sorted(self.edge1))
        e2 = tuple(sorted(self.edge2))
        edges_sorted = sorted([e1, e2])
        return f"{edges_sorted[0]}_{edges_sorted[1]}"
