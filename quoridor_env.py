import time
from typing import List
from config import Config
from graph import GraphState
from action import (
    ActionSpace,
    Action,
    BlockedPlayerAction,
    PlayerAction,
    WallAction,
)
import random


class QuoridorEnv:
    def __init__(self):
        self.s = Config()

        self.graph_state = GraphState()
        self.action_space = ActionSpace()

        # trackers
        self.running = True
        self.turn = 1

    def _get_player_movement_actions(self) -> List[PlayerAction]:
        """Method to add all legal normal player moves to the list"""
        actions = []
        y, x = self.graph_state.player_pos[self.to_move]

        for idx, (name, movement) in enumerate(
            self.action_space.player_movement.items()
        ):
            dy, dx = movement
            opponent = 0 if self.to_move == 0 else 1
            if (y + dy, x + dx) == self.graph_state.player_pos[opponent]:  # blocked
                self.actions.extend(self._get_player_blocked_actions())
            elif self.graph_state.is_edge((y, x), (y + dy, x + dx)):
                actions.append(PlayerAction(name=name, idx=idx, dx=dx, dy=dy))

        return actions

    def _get_player_blocked_actions(self) -> List[BlockedPlayerAction]:
        special_moves = []
        return special_moves

    def _get_wall_actions(self) -> List[WallAction]:
        if not self.graph_state.walls_left[self.to_move]:
            return []
        return self.graph_state.get_all_wall_moves()

    def get_all_legal_actions(self) -> List[Action]:
        """Method to get all legal_actions"""
        valid_actions = self._get_player_movement_actions() + self._get_wall_actions()

        return valid_actions

    def check_win(self):
        if (
            self.graph_state.goal_y[self.to_move]
            == self.graph_state.player_pos[self.to_move][0]
        ):
            self.running = False
            print(f"Player {self.to_move +1} won!!")
            return True
        return False

    def _execute_player_movement(self, action: PlayerAction | BlockedPlayerAction):
        y, x = self.graph_state.player_pos[self.to_move]
        self.graph_state.player_pos[self.to_move] = [y + action.dy, x + action.dx]

    def _execute_wall_action(self, action: WallAction):
        self.graph_state.execute_wall_action(action=action)
        self.graph_state.walls_left[self.to_move] -= 1

    def use_action(self, action: Action):
        if isinstance(action, PlayerAction):
            self._execute_player_movement(action=action)
        elif isinstance(action, BlockedPlayerAction):
            self._execute_player_movement(action=action)
        elif isinstance(action, WallAction):
            self._execute_wall_action(action=action)

    def game_loop(self):
        while self.running:

            # Player 1
            self.to_move = self.s.P1
            actions: List[Action] = self.get_all_legal_actions()
            p1_action: Action = random.choice(actions)  # random for now
            self.use_action(p1_action)
            self.graph_state.print_state()

            if self.check_win():
                break
            # End Player 1

            time.sleep(2)

            # Player 2
            self.to_move = self.s.P2
            actions: List[Action] = self.get_all_legal_actions()
            p2_action: Action = random.choice(actions)  # random for now
            self.use_action(p2_action)
            self.graph_state.print_state()
            if self.check_win():
                break
            time.sleep(2)
            # End Player 2

            # After turns
            self.turn += 1


# board example 5x5

# 0|0|0|0|0
# - - - - -
# X|0|0|0|0
# - - - - -
# 0|0|0|0|0
# - - - - -
# 0|0|0|X|0
# - - - - -
# 0|0|0|0|0


# TODO player to player collision
# TODO validity of wall based on astar or anything
# TODO special moves
# TOOD update graph structure

if __name__ == "__main__":
    game_env = QuoridorEnv()
    game_env.game_loop()
