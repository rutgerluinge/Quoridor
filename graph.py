from dataclasses import dataclass, field
from typing import Tuple, Dict, List
from colorama import Fore
import numpy as np
from copy import deepcopy
from collections import deque
from action import ActionSpace, WallAction
from config import Config


@dataclass(slots=True)
class GraphState:
    config: Config = field(default_factory=Config)
    graph: Dict[Tuple[int, int], List[Tuple[int, int]]] = field(init=False)

    player_pos: List[int] = field(init=False)
    goal_y: List[int] = field(init=False)
    walls_left: List[int] = field(init=False)

    placed_walls: set[tuple[tuple[int, int], tuple[int, int]]] = field(init=False)

    def __post_init__(self):
        """Method which gets called after init, can also be used to reset the state"""
        N, B = self.config.N, self.config.B
        c = N // 2

        self.player_pos = [[0, c], [N - 1, c]]
        self.goal_y = [N - 1, 0]
        self.walls_left = [B, B]

        self.placed_walls = set()

        self.construct_fc_graph()

    def construct_fc_graph(self):
        """
        Method which generates the fully connected graph,
        meaning that no walls have been placed, and thus all neigboring tiles are connected
        """
        self.graph = {}
        for y in range(self.config.N):
            for x in range(self.config.N):
                neighbors = []
                if y > 0:
                    neighbors.append((y - 1, x))
                if y < self.config.N - 1:
                    neighbors.append((y + 1, x))
                if x > 0:
                    neighbors.append((y, x - 1))
                if x < self.config.N - 1:
                    neighbors.append((y, x + 1))
                self.graph[(y, x)] = neighbors

    def reset(self):
        """Metho to re-initialise the GraphState"""
        self.__post_init__()

    def is_edge(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> bool:
        """Method which returns a boolean whether 2 tiles are connected aka no wall between them"""
        if con_list := self.graph.get(pos1):
            if pos2 in con_list:
                return True
        return False

    def possible_wall(self, wall: WallAction) -> bool:
        """Method which returns a boolean whether a wall can be placed (see WallIndex)"""
        if not self.is_edge(wall.edge1[0], wall.edge1[1]) or not self.is_edge(
            wall.edge2[0], wall.edge2[1]
        ):
            return False
        # at this point the wall can be placed, but we have to check for crossing
        if self.wall_is_crossed(wall):
            return False

        if self.wall_blocks_players(wall):
            return False

        return True

    def remove_connection(self, pos1: Tuple[int, int], pos2: Tuple[int, int]):
        """Method to remove a graph connection"""
        if con_list := self.graph.get(pos1):
            if pos2 in con_list:
                con_list.remove(pos2)

        if con_list := self.graph.get(pos2):
            if pos1 in con_list:
                con_list.remove(pos1)

    def execute_wall_action(self, action: WallAction):
        """Method to place wall, input can either be the formatted move string, or a WallAction object"""
        edge1, edge2 = action.edge1, action.edge2

        self.remove_connection(edge1[0], edge1[1])
        self.remove_connection(edge2[0], edge2[1])

        self.placed_walls.add(((edge1[0], edge1[1]), (edge2[0], edge2[1])))

    def wall_is_crossed(self, new_wall: WallAction) -> bool:
        """Method to check if is crossed by piece, there is most likely a problem here as im not sure if the points are ordered correctly"""
        edge_1, edge_2 = new_wall.edge1, new_wall.edge2
        p1, p2 = edge_1[0], edge_1[1]
        p3, p4 = edge_2[0], edge_2[1]

        crossed = ((p1, p3), (p2, p4))

        if crossed in self.placed_walls:
            return True
        return False

    def wall_blocks_players(self, new_wall: WallAction) -> bool:
        """Cool method to check if a potential move is possible, aka blocks a person
        BUG: either in here, or in how i show the state"""
        graph_copy = deepcopy(self.graph)

        graph_copy.get(new_wall.edge1[0]).remove(new_wall.edge1[1])
        graph_copy.get(new_wall.edge2[0]).remove(new_wall.edge2[1])

        def can_reach_goal_row(start: Tuple[int, int], goal_row: int) -> bool:
            """BFS: can we reach any node whose row index == goal_row"""
            start = tuple(start)
            visited = {start}
            queue = deque([start])

            while queue:
                node = queue.popleft()
                r, c = node  # assuming node = (row, col)
                if r == goal_row:
                    return True
                for nb in graph_copy.get(node, []):
                    if nb not in visited:
                        visited.add(nb)
                        queue.append(nb)
            return False

        for (
            pos,
            goal,
        ) in zip(self.player_pos, self.goal_y):
            if not can_reach_goal_row(start=(pos[0], pos[1]), goal_row=goal):
                return True
        return False

    def get_all_wall_moves(self) -> List[WallAction]:
        """Method to return all possible wall placement moves, both by movename, and Wall"""
        wall_moves: List[WallAction] = []

        # horizontal moves
        idx = ActionSpace.wall_horizontal_idx_start
        for row_idx in range(self.config.N - 1):  # -1 because a wall is 2 wide
            for col_idx in range(self.config.N - 1):
                action = WallAction(
                    name="",  # gets reinitialised by __post_init__
                    idx=idx,
                    edge1=[(row_idx, col_idx), (row_idx + 1, col_idx)],
                    edge2=[(row_idx, col_idx + 1), (row_idx + 1, col_idx + 1)],
                )
                if self.possible_wall(action):
                    wall_moves.append(action)
                idx += 1

        # vertical moves
        idx = ActionSpace.wall_vertical_idx_start
        for row_idx in range(self.config.N - 1):  # -1 because a wall is 2 wide
            for col_idx in range(self.config.N - 1):
                action = WallAction(
                    name="",  # gets reinitialised by __post_init__
                    idx=idx,
                    edge1=[(row_idx, col_idx), (row_idx, col_idx + 1)],
                    edge2=[(row_idx + 1, col_idx), (row_idx + 1, col_idx + 1)],
                )
                if self.possible_wall(action):
                    wall_moves.append(action)
                idx += 1

        return wall_moves

    def print_state(self):
        """Method to print the state to the terminal in a very nice way ;) if you are ambigious, create an UI PR!"""
        print("\033[H\033[J", end="")  # to sort of seem like redraw!

        # Helpers for plotting selecting and coloring the bars
        def _print_horizontal_bars(r_idx):
            horizontal_string = ""
            for c_idx in range(self.config.N):
                if (r_idx + 1, c_idx) in self.graph.get((r_idx, c_idx)):
                    color = Fore.WHITE
                else:
                    color = Fore.RED
                horizontal_string += color + "- "
            print(horizontal_string + Fore.RESET)

        def _print_vertical_bar(r_idx, c_idx, end=""):
            if (r_idx, c_idx + 1) in self.graph.get((r_idx, c_idx)):
                color = Fore.WHITE
            else:
                color = Fore.RED
            print(color + "|" + Fore.RESET, end=end)

        def _print_cell(r_idx, c_idx):
            if np.array_equal((r_idx, c_idx), self.player_pos[0]):
                print(Fore.GREEN + "X", end="")
            elif np.array_equal((r_idx, c_idx), self.player_pos[1]):
                print(Fore.CYAN + "X", end="")
            else:
                print(Fore.WHITE + " ", end="")

        def _print_vertical_and_cells(r_idx):
            for c_idx in range(self.config.N - 1):
                _print_cell(r_idx, c_idx)
                _print_vertical_bar(r_idx, c_idx)
            _print_cell(r_idx, self.config.N - 1)
            print()

        # Main draw loop :)
        for row_idx in range(self.config.N - 1):
            _print_vertical_and_cells(row_idx)
            _print_horizontal_bars(row_idx)
        _print_vertical_and_cells(self.config.N - 1)
