from typing import List
from graph import GraphState
from bots.bot import QuoridorBot
from action import Action, WallAction, PlayerAction, BlockedPlayerAction
import random


class RandomBot(QuoridorBot):
    def __init__(self, player_id: int):
        super().__init__(player_id)

    def select_move(self, state: GraphState, legal_actions: List[Action]) -> Action:
        return random.choice(legal_actions)
