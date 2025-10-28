from dataclasses import dataclass


@dataclass
class Config:
    N:int = 5  # total size (NxN) of spaces where a pawn can stand
    B:int = 10  # boards per player to place
    P1:int = 0  # player id 1
    P2:int = 1  # player id 2
