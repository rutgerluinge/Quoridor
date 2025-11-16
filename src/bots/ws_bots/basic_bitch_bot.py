from dataclasses import dataclass
import random
from typing import List, Tuple
from venv import logger
from action import Action, MovementAction
from configs import Graph, Pos
from graph_state import GraphState
from bots.quoridor_bot import QuoridorBot

import networkx as nx


@dataclass
class Player:
    id: int
    position: Pos
    goal_positions: List[Pos]
    available_walls: int


@dataclass
class GameState:
    player: Player
    opponent: Player
    graph: Graph
    placed_walls: List[Tuple[Pos, Pos]]
    nx_graph: nx.Graph = None

    def __post_init__(self):
        self.__init_nx_graph()

    def __init_nx_graph(self):
        G = nx.Graph()
        for node, neighbors in self.graph.items():
            for nbr in neighbors:
                G.add_edge(node, nbr)
        # Remove edges that are blocked by already placed wall segments
        # Each placed wall segment is a pair of adjacent positions (u, v).
        if self.placed_walls:
            for seg in self.placed_walls:
                try:
                    u, v = seg
                except Exception:
                    # Skip malformed entries defensively
                    logger.warning("Malformed wall segment in placed_walls: %s", seg)
                    continue
                if G.has_edge(u, v):
                    G.remove_edge(u, v)
        self.nx_graph = G

    def shortest_path(self, start: Pos, goal: Pos) -> List[Pos]:
        try:
            path = nx.shortest_path(self.nx_graph, source=start, target=goal)
            return path
        except nx.NetworkXNoPath:
            logger.warning("No path found from %s to %s", start, goal)
            return []  # No path found


class BasicBitchBot(QuoridorBot):

    def __init__(self, player_id: int):
        self.game_state: GameState = None
        super().__init__(player_id)

    @staticmethod
    def __str__() -> str:
        return "Basic Bitch Bot"

    def reset(self):
        self.game_state = None

    def select_move(self, state: GraphState, legal_actions: List[Action]) -> Action:
        self._update_game_state(state)

        legal_move_actions = [
            action for action in legal_actions if isinstance(action, MovementAction)
        ]
        current_player_position = self.game_state.player.position
        target_positions = self.game_state.player.goal_positions

        shortest_route = None
        for target_position in target_positions:
            route = self.game_state.shortest_path(
                current_player_position, target_position
            )
            if shortest_route is None or (route and len(route) < len(shortest_route)):
                shortest_route = route

        desired_next_position = shortest_route[1]
        desired_dx = desired_next_position[0] - current_player_position[0]
        desired_dy = desired_next_position[1] - current_player_position[1]

        matching_location_actions = [
            action
            for action in legal_move_actions
            if (action.dx, action.dy) == (desired_dx, desired_dy)
        ]
        if matching_location_actions:
            return matching_location_actions[0]

        # Fallback
        logger.warning(
            "No matching move action found for desired next position: %s",
            desired_next_position,
        )
        return random.choice(legal_actions)

    # Removed stray incomplete function definition
    def _update_game_state(self, state: GraphState):
        player = self._init_player(state, self.player_id)
        opponent = self._init_player(state, 1 - self.player_id)

        self.game_state = GameState(
            player=player,
            opponent=opponent,
            graph=state.graph,
            placed_walls=state.placed_walls,
        )

    def _init_player(self, state: GraphState, player_id: int) -> Player:
        return Player(
            id=player_id,
            position=state.player_pos[player_id],
            available_walls=state.walls_left[player_id],
            goal_positions=[
                (x, state.goal_y[player_id]) for x in range(state.config.N)
            ],
        )
