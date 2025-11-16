from __future__ import annotations

from collections import deque
from typing import Dict, List, Deque, Optional

import random

from configs import Graph, Pos
from graph_state import GraphState
from bots.quoridor_bot import QuoridorBot
from action import Action, MovementAction, BlockedMovementAction


class WalkBot(QuoridorBot):
    """
    A simple bot that walks along a shortest path (BFS) toward its goal row.
    """

    def __init__(self, player_id: int) -> None:
        super().__init__(player_id)

    @staticmethod
    def __str__() -> str:
        return "BFS Walk Bot"

    # ---------- BFS utilities ----------

    @staticmethod
    def _reconstruct_path(parent: Dict[Pos, Optional[Pos]], end: Pos) -> List[Pos]:
        path: List[Pos] = [end]
        cur = parent[end]
        while cur is not None:
            path.append(cur)
            cur = parent[cur]
        path.reverse()
        return path

    @staticmethod
    def bfs_shortest_path_to_goal(graph: Graph, start: Pos, goal_y: int) -> List[Pos]:
        """
        Find the shortest path from `start` to any node with y == goal_y.
        Returns a list of positions from start to goal (inclusive).
        Raises AssertionError if no path exists (should be impossible in valid Quoridor states).
        """
        if start[0] == goal_y:
            return [start]

        queue: Deque[Pos] = deque([start])
        parent: Dict[Pos, Optional[Pos]] = {start: None}
        visited = {start}

        while queue:
            node = queue.popleft()

            for nbr in graph.get(node, []):
                if nbr in visited:
                    continue
                visited.add(nbr)
                parent[nbr] = node

                if len(nbr) > 1 and nbr[0] == goal_y:
                    return WalkBot._reconstruct_path(parent, nbr)

                queue.append(nbr)

        # In a valid game state this should never happen.
        raise AssertionError(
            "Unreachable goal: game logic/state is inconsistent. walk_bot"
        )

    def reset(self):
        return super().reset()

    # ---------- Policy ----------

    def select_move(self, state: GraphState, legal_actions: List[Action]) -> Action:
        """
        Choose a walking move that advances along a shortest path toward the goal row.
        Falls back to a random walking move if something unexpected happens.
        """
        # Current position and goal row for this player
        pos: Pos = tuple(
            state.player_pos[self.player_id]
        )  # y, x # type: ignore[assignment]
        pos = (int(pos[0]), int(pos[1]))  # y, x
        goal_y: int = int(state.goal_y[self.player_id])  # y

        # Only consider walking-type actions for this bot
        # If any blocked walking moves exist, play one immediately (random if multiple) #this is just to show the possibilities, this move is OP!
        blocked_moves = [
            move for move in legal_actions if isinstance(move, BlockedMovementAction)
        ]
        if blocked_moves and random.random() > 0.5:
            return random.choice(blocked_moves)

        # Otherwise consider normal walking moves
        walk_moves: List[MovementAction] = [
            move for move in legal_actions if isinstance(move, MovementAction)
        ]

        if not walk_moves:
            return random.choice(legal_actions)

        path = self.bfs_shortest_path_to_goal(state.graph, pos, goal_y)

        # First step along the shortest path
        next_step = path[1]
        dx = next_step[1] - pos[1]  # x delta
        dy = next_step[0] - pos[0]  # y delta

        # Match the action whose (dx, dy) equals the needed step
        for move in walk_moves:
            if getattr(move, "dx", None) == dx and getattr(move, "dy", None) == dy:
                return move

        # Fallback: something desynced; choose any walking move
        return random.choice(walk_moves)
