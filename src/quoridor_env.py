import time
from typing import List
from bots.bot import QuoridorBot
from bots.random_bot import RandomBot
from bots.walk_bot import WalkBot
from config import Config
from graph import GraphState
from action import (
    ActionSpace,
    Action,
    BlockedPlayerAction,
    PlayerAction,
    WallAction,
)


class QuoridorEnv:
    def __init__(self):
        self.s = Config()

        self.state = GraphState()
        self.action_space = ActionSpace()

        # trackers
        self.running = True
        self.turn = 1

    def _get_player_movement_actions(self) -> List[PlayerAction]:
        """Method to add all legal normal player moves to the list"""
        actions = []
        y, x = self.state.player_pos[self.to_move]

        for idx, (name, movement) in enumerate(
            self.action_space.player_movement.items()
        ):
            dy, dx = movement
            if not self.state.is_edge((y, x), (y + dy, x + dx)):
                continue
            # at this point move is possible (is an edge)
            opponent = 1 - self.to_move
            if (y + dy, x + dx) == self.state.player_pos[opponent]:  # blocked
                actions.extend(self._get_player_blocked_actions())
                continue

            actions.append(PlayerAction(name=name, idx=idx, dx=dx, dy=dy))

        return actions

    def _get_player_blocked_actions(self) -> List[BlockedPlayerAction]:
        """Method to retrieve all special (blocked) moves
        At this point in call, we assume (earlier checked) that the edge between player and opponent is valid
        """
        player_pos = self.state.player_pos[self.to_move]
        opponent = self.state.player_pos[1 - self.to_move]

        dy = opponent[0] - player_pos[0]
        dx = opponent[1] - player_pos[1]

        blocked_moves: List[BlockedPlayerAction] = []
        jump_dy, jump_dx = 2 * dy, 2 * dx

        moves_vals = list(ActionSpace.blocked_movement.values())
        moves_keys = list(ActionSpace.blocked_movement.keys())
        start_idx = ActionSpace.blocked_movement_idx_start

        # Jumping moves
        if self.state.is_edge(
            pos1=opponent, pos2=(player_pos[0] + jump_dy, player_pos[1] + jump_dx)
        ):
            idx = moves_vals.index((jump_dy, jump_dx))
            jump_move = BlockedPlayerAction(
                name=moves_keys[idx],
                idx=start_idx + idx,
                dx=jump_dx,
                dy=jump_dy,
            )
            blocked_moves.append(jump_move)

        # Diagonal moves
        diagonal_dys = [-1, 1] if dx else []
        diagonal_dxs = [-1, 1] if dy else []
        for diagonal_dy in diagonal_dys:
            idx = moves_vals.index((diagonal_dy, dx))
            if self.state.is_edge(opponent, (opponent[0] + diagonal_dy, opponent[1])):
                diagonal_move = BlockedPlayerAction(
                    name=moves_keys[idx], idx=start_idx + idx, dx=dx, dy=diagonal_dy
                )
                blocked_moves.append(diagonal_move)

        for diagonal_dx in diagonal_dxs:
            idx = moves_vals.index((dy, diagonal_dx))
            if self.state.is_edge(opponent, (opponent[0], opponent[1] + diagonal_dx)):
                diagonal_move = BlockedPlayerAction(
                    name=moves_keys[idx], idx=start_idx + idx, dx=diagonal_dx, dy=dy
                )
                blocked_moves.append(diagonal_move)

        return blocked_moves

    def _get_wall_actions(self) -> List[WallAction]:
        if not self.state.walls_left[self.to_move]:
            return []
        return self.state.get_all_wall_moves()

    def get_all_legal_actions(self) -> List[Action]:
        """Method to get all legal_actions"""
        valid_actions = self._get_player_movement_actions() + self._get_wall_actions()

        return valid_actions

    def check_win(self):
        if self.state.goal_y[self.to_move] == self.state.player_pos[self.to_move][0]:
            self.running = False
            print(f"Player {self.to_move +1} won!!")
            return True
        return False

    def _execute_player_movement(self, action: PlayerAction | BlockedPlayerAction):
        y, x = self.state.player_pos[self.to_move]
        self.state.player_pos[self.to_move] = (y + action.dy, x + action.dx)

    def _execute_wall_action(self, action: WallAction):
        self.state.execute_wall_action(action=action)
        self.state.walls_left[self.to_move] -= 1

    def use_action(self, action: Action):
        if isinstance(action, PlayerAction):
            self._execute_player_movement(action=action)
        elif isinstance(action, BlockedPlayerAction):
            self._execute_player_movement(action=action)
        elif isinstance(action, WallAction):
            self._execute_wall_action(action=action)

    def game_loop(self, player_1: QuoridorBot, player_2: QuoridorBot):
        time.sleep(0.5)
        while self.running:

            # Player 1
            self.to_move = self.s.P1
            actions: List[Action] = self.get_all_legal_actions()
            p1_action: Action = player_1.select_move(
                state=self.state, legal_actions=actions
            )
            self.use_action(p1_action)
            self.state.draw_board()

            if self.check_win():
                break
            # End Player 1

            time.sleep(2)

            # Player 2
            self.to_move = self.s.P2
            actions: List[Action] = self.get_all_legal_actions()
            p2_action: Action = player_2.select_move(
                state=self.state, legal_actions=actions
            )
            print(f"actions: {actions}, chosen action {p2_action}")
            self.use_action(p2_action)

            self.state.draw_board()
            if self.check_win():
                break
            time.sleep(2)
            # End Player 2

            # After turns
            self.turn += 1


# TODO player to player collision

if __name__ == "__main__":
    game_env = QuoridorEnv()

    player_1 = WalkBot(player_id=0)
    player_2 = WalkBot(player_id=1)

    game_env.game_loop(player_1, player_2)
