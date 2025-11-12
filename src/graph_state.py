from dataclasses import dataclass, field
from typing import List, Dict, Set
from colorama import Fore
from collections import deque

from action import ActionSpace, WallAction
from configs import Config, Graph, Pos


@dataclass(slots=True)
class GraphState:
    """
    Represents the full board state for Quoridor:
    - Graph of traversable edges between tiles
    - Player positions
    - Goal rows per player
    - Remaining walls and placed wall segments
    """

    config: Config = field(default_factory=Config)
    graph: Graph = field(init=False)

    player_pos: List[Pos] = field(init=False)
    goal_y: List[int] = field(init=False)
    walls_left: List[int] = field(init=False)

    # Each element is ((r1, c1), (r2, c2)) describing a wall segment
    placed_walls: Set[tuple[Pos, Pos]] = field(init=False)

    def __post_init__(self) -> None:
        self._init_state()

    # ---------- State initialisation ----------

    def _init_state(self) -> None:
        """Initialise or reset the full board state."""
        N, B = self.config.N, self.config.W
        center_col = N // 2

        # Player 0 starts at top row, Player 1 at bottom row
        self.player_pos = [(0, center_col), (N - 1, center_col)]
        self.goal_y = [N - 1, 0]  # rows they need to reach
        self.walls_left = [B, B]

        self.placed_walls = set()
        self._construct_graph()

    def _construct_graph(self) -> None:
        """
        Generate the base graph with all neighbouring tiles connected (no walls yet).
        Each node is (row, col) and neighbours are its 4-neighbourhood.
        """
        N = self.config.N
        self.graph = {}
        for y in range(N):
            for x in range(N):
                neighbors = []
                if y > 0:
                    neighbors.append((y - 1, x))
                if y < N - 1:
                    neighbors.append((y + 1, x))
                if x > 0:
                    neighbors.append((y, x - 1))
                if x < N - 1:
                    neighbors.append((y, x + 1))
                self.graph[(y, x)] = neighbors

    def reset(self) -> None:
        """Reset the graph state to a new game."""
        self._init_state()

    # ---------- Graph / wall queries ----------

    def is_edge(self, pos1: Pos, pos2: Pos) -> bool:
        """
        Return True if two tiles are connected (i.e., there is no wall blocking).
        """
        return pos2 in self.graph.get(pos1, [])

    @staticmethod
    def remove_connection(graph: Graph, pos1: Pos, pos2: Pos) -> None:
        """
        Remove an undirected connection between pos1 and pos2 from the given graph.
        Works both for list-based and set-based adjacency.
        """
        neighbors1 = graph.get(pos1)
        if neighbors1 is not None and pos2 in neighbors1:
            neighbors1.remove(pos2)

        neighbors2 = graph.get(pos2)
        if neighbors2 is not None and pos1 in neighbors2:
            neighbors2.remove(pos1)

    # ---------- Wall placement logic ----------

    def possible_wall(self, wall: WallAction) -> bool:
        """
        Check whether a wall can be placed:
        - both edges still exist in the graph
        - wall does not cross another wall
        - wall does not completely block a player's path to their goal row
        """
        if not self.is_edge(wall.edge1[0], wall.edge1[1]) or not self.is_edge(
            wall.edge2[0], wall.edge2[1]
        ):
            return False

        if self._wall_is_crossed(wall):
            return False

        if self._wall_blocks_any_player(wall):
            return False

        return True

    def execute_wall_action(self, action: WallAction) -> None:
        """
        Place a wall in the current state:
        - remove the corresponding connections from the graph
        - register the wall segments so future crossings can be detected
        """
        edge1, edge2 = action.edge1, action.edge2

        self.remove_connection(self.graph, edge1[0], edge1[1])
        self.remove_connection(self.graph, edge2[0], edge2[1])

        # Store the two segments that form this wall
        self.placed_walls.add((edge1[0], edge1[1]))
        self.placed_walls.add((edge2[0], edge2[1]))

    def _wall_is_crossed(self, new_wall: WallAction) -> bool:
        """
        Check whether `new_wall` would cross an existing wall.
        We do this by reconstructing the two 'crossing' segments and checking
        if they're in placed_walls.

        For a horizontal vs vertical crossing, the placed segments are exactly:
        ((p1, p3), (p2, p4)) where:
          - new_wall.edge1 = [p1, p2]
          - new_wall.edge2 = [p3, p4]
        """
        edge_1, edge_2 = new_wall.edge1, new_wall.edge2
        p1, p2 = edge_1[0], edge_1[1]
        p3, p4 = edge_2[0], edge_2[1]

        crossed_seg1 = (p1, p3)
        crossed_seg2 = (p2, p4)

        return crossed_seg1 in self.placed_walls and crossed_seg2 in self.placed_walls

    def _wall_blocks_any_player(self, new_wall: WallAction) -> bool:
        """
        Simulate placing this wall and check if *any* player loses all paths
        to their goal row.
        """
        # Make a shallow copy of the adjacency structure
        graph_copy: Dict[Pos, set] = {
            node: set(neighs) for node, neighs in self.graph.items()
        }

        # Remove adjacencies for both segments of the new wall
        a1, b1 = new_wall.edge1
        a2, b2 = new_wall.edge2
        self.remove_connection(graph_copy, a1, b1)
        self.remove_connection(graph_copy, a2, b2)

        def can_reach_goal_row(start: Pos, goal_row: int) -> bool:
            """BFS to check reachability to any node with row == goal_row."""
            start = tuple(start)
            visited = {start}
            queue = deque([start])

            while queue:
                node = queue.popleft()
                r, _ = node
                if r == goal_row:
                    return True
                for nb in graph_copy.get(node, []):
                    if nb not in visited:
                        visited.add(nb)
                        queue.append(nb)
            return False

        for pos, goal in zip(self.player_pos, self.goal_y):
            if not can_reach_goal_row(start=(pos[0], pos[1]), goal_row=goal):
                return True

        return False

    def get_all_wall_moves(self) -> List[WallAction]:
        """
        Return all legal wall placement moves for the current state.
        """
        wall_moves: List[WallAction] = []

        N = self.config.N

        # Horizontal walls
        idx = ActionSpace.wall_horizontal_idx_start
        for row_idx in range(N - 1):
            for col_idx in range(N - 1):
                action = WallAction(
                    name="",  # filled by __post_init__ of WallAction
                    idx=idx,
                    edge1=[(row_idx, col_idx), (row_idx + 1, col_idx)],
                    edge2=[(row_idx, col_idx + 1), (row_idx + 1, col_idx + 1)],
                )
                if self.possible_wall(action):
                    wall_moves.append(action)
                idx += 1

        # Vertical walls
        idx = ActionSpace.wall_vertical_idx_start
        for row_idx in range(N - 1):
            for col_idx in range(N - 1):
                action = WallAction(
                    name="",  # filled by __post_init__ of WallAction
                    idx=idx,
                    edge1=[(row_idx, col_idx), (row_idx, col_idx + 1)],
                    edge2=[(row_idx + 1, col_idx), (row_idx + 1, col_idx + 1)],
                )
                if self.possible_wall(action):
                    wall_moves.append(action)
                idx += 1

        return wall_moves

    # ---------- Drawing ----------

    def draw_board(self) -> None:
        """
        My very pretty draw method :)
        Feel free to make a pr or something to improve this
        """
        print("\033[H\033[J", end="")  # Clear-ish screen kinda cool tbh

        def _print_horizontal_bars(r_idx: int) -> None:
            horizontal_string = ""
            for c_idx in range(self.config.N):
                if (r_idx + 1, c_idx) in self.graph.get((r_idx, c_idx), []):
                    color = Fore.WHITE
                else:
                    color = Fore.RED
                horizontal_string += color + "─ "
            print(horizontal_string + Fore.RESET)

        def _print_vertical_bar(r_idx: int, c_idx: int, end: str = "") -> None:
            if (r_idx, c_idx + 1) in self.graph.get((r_idx, c_idx), []):
                color = Fore.WHITE
            else:
                color = Fore.RED
            print(color + "│" + Fore.RESET, end=end)

        def _print_cell(r_idx: int, c_idx: int) -> None:
            pos = (r_idx, c_idx)
            if pos == self.player_pos[0]:
                print(Fore.GREEN + "X", end="")
            elif pos == self.player_pos[1]:
                print(Fore.CYAN + "X", end="")
            else:
                print(Fore.WHITE + " ", end="")

        def _print_vertical_and_cells(r_idx: int) -> None:
            for c_idx in range(self.config.N - 1):
                _print_cell(r_idx, c_idx)
                _print_vertical_bar(r_idx, c_idx)
            _print_cell(r_idx, self.config.N - 1)
            print()

        for row_idx in range(self.config.N - 1):
            _print_vertical_and_cells(row_idx)
            _print_horizontal_bars(row_idx)
        _print_vertical_and_cells(self.config.N - 1)
