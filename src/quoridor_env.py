import time
from typing import List

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from copy import deepcopy

from bots.quoridor_bot import QuoridorBot
from configs import Config
from graph_state import GraphState
from action import (
    ActionSpace,
    Action,
    BlockedMovementAction,
    MovementAction,
    WallAction,
)


class QuoridorEnv:
    """
    Game environment for Quoridor.

    Responsibilities:
    - Maintain whose turn it is
    - Ask GraphState for legal actions
    - Let bots choose actions (with timeout)
    - Apply actions to state
    - Detect wins
    - Game Loop! while capturing
    """

    def __init__(self) -> None:
        self.s = Config()

        self.state = GraphState()
        self.action_space = ActionSpace()

        self.running: bool = True
        self.turn: int = 1
        self.to_move: int = self.s.P1  # start with player 1 by default

    def reset(self) -> None:
        self.state.reset()
        self.turn = 1
        self.running = True
        self.to_move = self.s.P1

    # ---------- Legal move generation ----------

    def _get_player_movement_actions(
        self,
    ) -> List[MovementAction | BlockedMovementAction]:
        """
        Return all legal pawn movement actions (normal + blocked moves) for the player to move.
        """
        actions: List[MovementAction | BlockedMovementAction] = []
        y, x = self.state.player_pos[self.to_move]

        for idx, (name, movement) in enumerate(
            self.action_space.player_movement.items()
        ):
            dy, dx = movement

            # Edge must exist (no wall in between, and on-board)
            if not self.state.is_edge((y, x), (y + dy, x + dx)):
                continue

            # Opponent directly in the way -> special 'blocked' moves (jump / diagonals)
            opponent = 1 - self.to_move
            if (y + dy, x + dx) == self.state.player_pos[opponent]:
                actions.extend(self._get_player_blocked_actions())
                continue

            actions.append(MovementAction(name=name, idx=idx, dx=dx, dy=dy))

        return actions

    def _get_player_blocked_actions(self) -> List[BlockedMovementAction]:
        """
        Retrieve all special (blocked) moves when the pawn is directly facing the opponent.
        Assumes the edge between player and opponent is valid.
        """
        player_pos = self.state.player_pos[self.to_move]
        opponent_pos = self.state.player_pos[1 - self.to_move]

        dy = opponent_pos[0] - player_pos[0]
        dx = opponent_pos[1] - player_pos[1]

        blocked_moves: List[BlockedMovementAction] = []
        jump_dy, jump_dx = 2 * dy, 2 * dx

        moves_vals = list(ActionSpace.blocked_movement.values())
        moves_keys = list(ActionSpace.blocked_movement.keys())
        start_idx = ActionSpace.blocked_movement_idx_start

        # ----- Jumping move -----
        if self.state.is_edge(
            pos1=opponent_pos,
            pos2=(player_pos[0] + jump_dy, player_pos[1] + jump_dx),
        ):
            # This (jump_dy, jump_dx) should be in blocked_movement, kinda cool logic
            idx = moves_vals.index((jump_dy, jump_dx))
            jump_move = BlockedMovementAction(
                name=moves_keys[idx],
                idx=start_idx + idx,
                dx=jump_dx,
                dy=jump_dy,
            )
            blocked_moves.append(jump_move)

        # If jump is possible, diagonals are not allowed
        if blocked_moves:
            return blocked_moves

        # ----- Diagonal moves -----
        diagonal_dys = [-1, 1] if dx else []
        diagonal_dxs = [-1, 1] if dy else []

        # Diagonal in Y direction (side steps up/down)
        for diagonal_dy in diagonal_dys:
            # Move (diagonal_dy, dx), still blocked_movement by design
            idx = moves_vals.index((diagonal_dy, dx))
            if self.state.is_edge(
                opponent_pos, (opponent_pos[0] + diagonal_dy, opponent_pos[1])
            ):
                diagonal_move = BlockedMovementAction(
                    name=moves_keys[idx],
                    idx=start_idx + idx,
                    dx=dx,
                    dy=diagonal_dy,
                )
                blocked_moves.append(diagonal_move)

        # Diagonal in X direction (side steps left/right)
        for diagonal_dx in diagonal_dxs:
            idx = moves_vals.index((dy, diagonal_dx))
            if self.state.is_edge(
                opponent_pos, (opponent_pos[0], opponent_pos[1] + diagonal_dx)
            ):
                diagonal_move = BlockedMovementAction(
                    name=moves_keys[idx],
                    idx=start_idx + idx,
                    dx=diagonal_dx,
                    dy=dy,
                )
                blocked_moves.append(diagonal_move)

        return blocked_moves

    def _get_wall_actions(self) -> List[WallAction]:
        """
        Return all legal wall actions for the player to move, considering remaining walls.
        """
        if not self.state.walls_left[self.to_move]:
            return []
        return self.state.get_all_wall_moves()

    def get_all_legal_actions(self) -> List[Action]:
        """
        Get all legal actions (movement + wall placement) for the player to move.
        """
        return list(self._get_player_movement_actions()) + list(
            self._get_wall_actions()
        )

    # ---------- Rule application ----------

    def check_win(self) -> bool:
        """
        Check if the player to move has reached their goal row.
        """
        player_row = self.state.player_pos[self.to_move][0]
        if self.state.goal_y[self.to_move] == player_row:
            self.running = False
            return True
        return False

    def _execute_player_movement(
        self, action: MovementAction | BlockedMovementAction
    ) -> None:
        """
        Apply a movement to the current player.
        """
        y, x = self.state.player_pos[self.to_move]
        self.state.player_pos[self.to_move] = (y + action.dy, x + action.dx)

    def _execute_wall_action(self, action: WallAction) -> None:
        """
        Apply a wall placement for the current player.
        """
        self.state.execute_wall_action(action=action)
        self.state.walls_left[self.to_move] -= 1

    def use_action(self, action: Action) -> None:
        """
        Apply the given action to the current state.
        """
        if isinstance(action, (MovementAction, BlockedMovementAction)):
            self._execute_player_movement(action=action)
        elif isinstance(action, WallAction):
            self._execute_wall_action(action=action)
        else:
            raise ValueError(f"Unknown action type: {type(action)}")

    # ---------- Bot interaction / game loop ----------

    def _draw(self) -> None:
        """Redraw the board and pause briefly."""
        self.state.draw_board()
        time.sleep(0.75)

    def _timed_select_move(
        self,
        bot: QuoridorBot,
        legal_actions: List[Action],
        executor: ThreadPoolExecutor,
        move_timeout: float,
    ):
        """
        Run bot.select_move with a timeout. Returns (ok, action).
        If timed out or crashed, returns (False, None).
        """
        future = executor.submit(
            bot.select_move,
            state=deepcopy(self.state),
            legal_actions=deepcopy(legal_actions),
        )
        try:
            return True, future.result(timeout=move_timeout)
        except FuturesTimeoutError:
            return False, None
        except Exception as e:
            # Treat crashes like a timeout: immediate loss for this bot.
            print(f"Exception in select_move for bot {bot.player_id}: {e}")
            return False, None

    def _play_single_turn(
        self,
        bot_to_move: QuoridorBot,
        bot_other: QuoridorBot,
        executor: ThreadPoolExecutor,
        move_timeout: float,
        visualise: bool,
    ) -> str | None:
        """
        Execute a single player's turn:
        - compute legal actions
        - ask the bot for a move (with timeout)
        - validate and apply the move
        - check for a win

        Returns:
            winner_id (str) if the game ended on this turn, else None.
        """
        actions = self.get_all_legal_actions()

        ok, chosen_action = self._timed_select_move(
            bot_to_move,
            legal_actions=actions,
            executor=executor,
            move_timeout=move_timeout,
        )

        if not ok:
            print(
                f"Player {bot_to_move.player_id} timed out or crashed. "
                f"Player {bot_other.player_id} wins."
            )
            self.running = False
            return bot_other.player_id

        if chosen_action not in actions:
            print(f"Illegal action chosen by Player {bot_to_move.player_id}:")
            print(chosen_action)
            self.running = False
            return bot_other.player_id

        self.use_action(chosen_action)

        if visualise:
            self._draw()

        if self.check_win():
            self.running = False
            return bot_to_move.player_id

        return None

    def game_loop(
        self,
        player_1: QuoridorBot,
        player_2: QuoridorBot,
        visualise: bool = True,
        move_timeout: float = 2.0,
    ) -> str:
        """
        Run a full game between two bots and return the winner's player_id.
        """
        self.reset()
        if visualise:
            self._draw()

        with ThreadPoolExecutor(max_workers=2) as executor:
            while self.running:
                # ---------- Player 1 ----------
                self.to_move = self.s.P1
                winner = self._play_single_turn(
                    bot_to_move=player_1,
                    bot_other=player_2,
                    executor=executor,
                    move_timeout=move_timeout,
                    visualise=visualise,
                )
                if winner is not None:
                    return winner

                # ---------- Player 2 ----------
                self.to_move = self.s.P2
                winner = self._play_single_turn(
                    bot_to_move=player_2,
                    bot_other=player_1,
                    executor=executor,
                    move_timeout=move_timeout,
                    visualise=visualise,
                )
                if winner is not None:
                    return winner

                self.turn += 1
                if self.turn >= self.s.MAX_MOVES:
                    return -1
