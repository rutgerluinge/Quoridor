from collections import deque
from math import inf
from typing import Deque, Dict, List, Optional
from configs import Graph, Pos
from graph_state import GraphState
from bots.template_bot import QuoridorBot
from action import Action, BlockedMovementAction, MovementAction, WallAction
import random
from copy import deepcopy


class WallPlaceBot(QuoridorBot):
    def __init__(self, player_id: int):
        super().__init__(player_id)

    @staticmethod
    def __str__() -> str:
        return "WallBot"

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
                    return WallPlaceBot._reconstruct_path(parent, nbr)

                queue.append(nbr)

        return None

    def reset(self):
        return super().reset()

    def select_move(self, state: GraphState, legal_actions: List[Action]) -> Action:
        # Partition actions once
        wall_acts = [a for a in legal_actions if isinstance(a, WallAction)]
        move_acts = [a for a in legal_actions if isinstance(a, MovementAction)]
        # You had this but didn't use it; keep if you need it elsewhere
        blocked_move_acts = [a for a in legal_actions if isinstance(a, BlockedMovementAction)]

        own_pos, opp_pos = (
            state.player_pos[self.player_id],
            state.player_pos[1 - self.player_id],
        )
        own_goal, opp_goal = (
            state.goal_y[self.player_id],
            state.goal_y[1 - self.player_id],
        )

        def path_len(gstate: GraphState, pos, goal) -> int:
            """Return shortest path length (nodes) or +inf if unreachable/empty."""
            path = self.bfs_shortest_path_to_goal(gstate.graph, pos, goal)
            if not path:
                return inf
            return len(path)

        # Current baseline
        opp_len = path_len(state, opp_pos, opp_goal)
        own_path = self.bfs_shortest_path_to_goal(state.graph, own_pos, own_goal)
        own_len = len(own_path) if own_path else inf
        diff = opp_len - own_len

        # ---------- Try to find a beneficial wall ----------
        best_wall: List[WallAction] = []
        best_improvement = 0  # new_diff - diff

        for candidate in wall_acts:
            tmp = deepcopy(state)
            # Assuming this applies the wall and keeps legality; it's from legal_actions
            tmp.execute_wall_action(candidate)

            new_opp_len = path_len(tmp, opp_pos, opp_goal)
            new_own_len = path_len(tmp, own_pos, own_goal)

            # If either side becomes unreachable (shouldn't happen for legal walls), skip it
            if new_opp_len is inf or new_own_len is inf:
                continue

            new_diff = new_opp_len - new_own_len
            improvement = new_diff - diff

            # We want to increase (own_len - opp_len) in our favor:
            # e.g., make opponent farther or us not much farther.
            if improvement > best_improvement:
                best_improvement = improvement
                best_wall = [candidate]
            elif improvement == best_improvement:
                best_wall.append(candidate)

        if best_wall and best_improvement > 0:
            return random.choice(best_wall)

        # ---------- Otherwise: walk along own shortest path ----------
        # If we have a valid path and at least one step, follow it
        walk_moves = move_acts + blocked_move_acts

        best_move: List[Action] = []
        shortest_distance = inf
        for move in walk_moves:
            dx = move.dx
            dy = move.dy
            new_pos = (own_pos[0] + dy, own_pos[1] + dx)
            distance = path_len(state, new_pos, own_goal)
            if distance < shortest_distance:
                shortest_distance = distance
                best_move = [move]
            elif distance == shortest_distance:
                best_move.append(move)

        # If no matching movement action (or no path), just pick any legal movement;
        # avoid accidentally choosing a wall when we intended to move.
        if best_move:
            return random.choice(best_move)

        # Absolute last resort: any legal action
        return random.choice(legal_actions)
