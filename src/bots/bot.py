from abc import ABC, abstractmethod
from typing import Any, List
from action import Action, WallAction, PlayerAction, BlockedPlayerAction
from graph import GraphState


class QuoridorBot(ABC):
    """Abstract Class to follow for your own bot creationg"""

    # this will be initialised to either be player 1 (idx =0) thus start player,
    # or player 2 (idx = 1) you have a differnet start pos and goal pos
    def __init__(self, player_id: int):
        self.player_id = player_id

    @abstractmethod
    def select_move(self, state: GraphState, legal_actions: List[Action]) -> Action:
        """Subclasses must implement this."""
        raise NotImplementedError

