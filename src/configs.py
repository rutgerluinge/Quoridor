from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class Config:
    N: int = 9  # total size (NxN) of spaces where a pawn can stand
    W: int = 9  # walls per player to place
    P1: int = 0  # player id 1
    P2: int = 1  # player id 2

    MAX_MOVES: int = 250  # cap


# Some used datatypes
Pos = Tuple[int]
Graph = Dict[Pos, List[Pos]]


@dataclass
class TournamentConfig:
    rounds = 10
    max_move_time = 1.0
