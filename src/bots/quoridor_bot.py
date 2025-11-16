from abc import ABC, abstractmethod
from typing import Any, List
from action import Action, WallAction, MovementAction, BlockedMovementAction
from graph_state import GraphState


class QuoridorBot(ABC):
    """Abstract Class to follow for your own bot creationg"""

    # this will be initialised to either be player 1 (idx =0) thus start player,
    # or player 2 (idx = 1) you have a differnet start pos and goal pos
    def __init__(self, player_id: int):
        self.player_id = player_id

    @staticmethod
    @abstractmethod
    def __str__() -> str:
        """Use an original name!"""
        raise NotImplementedError

    @abstractmethod
    def reset(self) -> None:
        """Reset any internal state between games, if needed. This gets called instead of creating a new bot instance, such that you could use tactics for countering your opponents playstyle"""
        pass

    @abstractmethod
    def select_move(self, state: GraphState, legal_actions: List[Action]) -> Action:
        """
        At this moment in the state, is your turn to move!
        Main method to implement with your bot logic
        :param state: current State of the game (as graph), see graph.py for details, this is a copy so you can do whatever!
        :param legal_actions: list of legal actions you can choose from, only return one of those or you get an instant loss this round!
        :return: Action to play this turn

        wall_actions = [a for a in legal_actions if isinstance(a, WallAction)]
        move_actions = [a for a in legal_actions if isinstance(a, MovementAction)]
        blocked_move_actions = [a for a in legal_actions if isinstance(a, BlockedMovementAction)]
        """

        raise NotImplementedError
