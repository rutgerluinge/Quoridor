from dataclasses import dataclass, field
import time
from typing import List, Tuple
import numpy as np
from colorama import Fore

@dataclass
class Settings:
    N = 5   #total size (NxN) of spaces where a pawn can stand
    B = 2   #boards per player to place
    P1 = 0  #player id 1
    P2 = 1  #player id 2

@dataclass(slots=True)
class State:
    s: Settings = field(default_factory=Settings)
    pos: np.ndarray = field(init=False)
    goal_y: np.ndarray = field(init=False)
    walls: np.ndarray = field(init=False)

    board: np.ndarray = field(init=False)  
    ver:   np.ndarray = field(init=False)  
    hor:   np.ndarray = field(init=False) 

    def __post_init__(self):
        N, B = self.s.N, self.s.B
        c = N // 2

        self.pos   = np.array([[0, c], [N - 1, c]], dtype=np.uint8)
        self.goal_y = np.array([N-1, 0], dtype=np.uint8)
        self.walls = np.array([B, B], dtype=np.uint8)

        self.board = np.zeros((N, N), dtype=np.int8)
     
        #track walls
        self.ver = np.zeros((N, N + 1), dtype=bool)
        self.hor = np.zeros((N + 1, N), dtype=bool)


    def print_state(self):
        #Kinda cooked and ugly but not to bad :)

        print("\033[H\033[J", end="") #to sort of seem like redraw!

        # Helpers for plotting selecting and coloring the bars
        def _print_horizontal_bars(idx):
            horizontal_string = ''.join([Fore.RED + ' -' if value else Fore.WHITE + ' -' for value in self.hor[idx]])
            print(horizontal_string + Fore.RESET)
        
        def _print_vertical_bar(r_idx, c_idx, end=''):
            color = Fore.RED if self.ver[r_idx][c_idx] else Fore.WHITE
            print(color + "|" + Fore.RESET, end=end)

        def _print_cell(r_idx, c_idx):
            if np.array_equal([r_idx, c_idx], self.pos[0]):
                print(Fore.GREEN + "X", end='')
            elif np.array_equal([r_idx, c_idx], self.pos[1]):
                print(Fore.CYAN + "X", end='')
            else:
                print(Fore.WHITE + " ", end='')

        # Main draw loop :) 
        for row_idx in range(self.s.N):
            _print_horizontal_bars(row_idx)

            for col_idx in range(self.s.N):
                _print_vertical_bar(row_idx, col_idx)
                _print_cell(row_idx, col_idx)

            _print_vertical_bar(row_idx, -1, end='\n')

        _print_horizontal_bars(-1) #last 


class ActionSpace:
    s = Settings()
    player_movement = {
        "up": (-1, 0), 
        "right": (0, 1), 
        "left": (0, -1), 
        "down": (1, 0)
    }
    special_movement_idx_start = len(player_movement) - 1
    special_movement = {
        "jump_up": (-2, 0),
        "jump_down": (2, 0),
        "jump_left": (0, -2),
        "jump_right": (0, 2),
        "up_left": (-1, -1),
        "up_right": (-1, 1),
        "down_left": (1, -1),
        "down_right": (1, 1),
    }

    wall_vertical_idx_start = special_movement_idx_start + len(special_movement)
    wall_vertical_space = (s.N-1) * (s.N+1)

    wall_horizontal_idx_start = wall_vertical_idx_start + wall_vertical_space
    wall_horizontal_space = (s.N-1) * (s.N+1)

    action_space = len(player_movement) + len(special_movement) + wall_vertical_space + wall_horizontal_space


class QuoridorEnv:
    def __init__(self):
        self.s = Settings()

        self.state: State = State()
        self.action_space = ActionSpace()
               
        #trackers
        self.running = True
        self.turn = 1

    def _check_move_validity(self, x:int, dx:int, y:int, dy:int) -> bool:
        #first check out of bounds
        new_y = y+dy
        new_x = x+dx
        if not (0 <= new_x < self.s.N and 0 <= new_y < self.s.N):
            return False
        
        #check if wall in the way
        if dx != 0:
            wall_offset = 0 if dx == -1 else 1
            if self.state.ver[new_y, x+wall_offset]:
                return False

        if dy != 0:
            wall_offset = 0 if dy == -1 else 1
            if self.state.hor[y+wall_offset, new_x]:
                return False

        return True
    
    
    def _get_normal_moves(self) -> Tuple[List[str], List[int]]:
        y, x = self.state.pos[self.to_move]
        move_names, indices = [], []

        for idx, (name, movement) in enumerate(
            self.action_space.player_movement.items()):
            dy, dx = movement
            if self._check_move_validity(int(x), dx, int(y), dy):
                move_names.append(name)
                indices.append(idx)

        return move_names, indices

    def _get_special_moves(self) -> Tuple[List[str], List[int]]:
        # Logic fo special moves when blocked TODO
        return [], []

    def _check_wall_validity(self, wall_move:str) -> bool:
        """checks if a wall would disturb the path"""
        # TODO astar?

        return True

    def _get_vertical_wall_moves(self) -> Tuple[List[str], List[int]]:
        if not self.state.walls[self.to_move]:
            return [], [] #no walls left..
        
        valid_move_ids = []
        valid_move_indices = []
        move_idx = self.action_space.wall_vertical_idx_start

        for row_idx in range(len(self.state.ver) - 1):  #-1 because walls are size 2
            for col_idx in range(len(self.state.ver[row_idx])):
                if self.state.ver[row_idx, col_idx] or self.state.ver[row_idx + 1, col_idx]:
                    #invalid move
                    move_idx += 1
                    continue
                move_name = f"ver_{col_idx}_{row_idx}"
                if not self._check_wall_validity(move_name):
                    move_idx += 1
                    continue

                valid_move_indices.append(move_idx)
                valid_move_ids.append(move_name)
                move_idx += 1

        return valid_move_ids, valid_move_indices

    def _get_horizontal_wall_moves(self):
        if not self.state.walls[self.to_move]:
            return [], [] #no walls left..
        
        valid_move_ids = []
        valid_move_indices = []
        move_idx = self.action_space.wall_horizontal_idx_start

        for row_idx in range(len(self.state.hor)):  
            for col_idx in range(len(self.state.hor[row_idx]) - 1): #-1 because walls are size 2
                if self.state.hor[row_idx, col_idx] or self.state.hor[row_idx, col_idx + 1]:    #check invalid
                    move_idx += 1
                    continue
                move_name = f"hor_{col_idx}_{row_idx}"
                if not self._check_wall_validity(move_name):
                    move_idx += 1
                    continue

                valid_move_indices.append(move_idx)
                valid_move_ids.append(move_name)
                move_idx += 1

        return valid_move_ids, valid_move_indices

    def get_all_legal_moves(self) -> Tuple[List[str], List[int]]:
        """Method to get all legal_moves (indices) of action space"""
        valid_move_ids = []
        valid_move_indices = []
        methods = [
            self._get_normal_moves,
            self._get_special_moves,
            self._get_horizontal_wall_moves,
            self._get_vertical_wall_moves
        ]

        for move_method in methods:
            move_id, move_idx = move_method()   #call the helper methods which retrieve valid moves
            valid_move_ids.extend(move_id)
            valid_move_indices.extend(move_idx)

        return valid_move_ids, valid_move_indices

    def check_win(self):
        if self.state.goal_y[self.to_move] == self.state.pos[self.to_move][0]: #0 is y
            self.running = False
            print(f"Player {self.to_move +1} won!!")
            return True


    def use_move(self, move_name:str):
        if (move := self.action_space.player_movement.get(move_name)):
            dy, dx = move
            y, x = self.state.pos[self.to_move]
            self.state.pos[self.to_move] = [int(y) + dy, int(x) + dx]
            return

        elif move_name in self.action_space.special_movement:
            return
        
        #if this fails for some reason a weird move id has snugged in... cannot bother to do safe guards..
        wall_orientation, col_idx, row_idx = move_name.split("_")
        col_idx, row_idx = int(col_idx), int(row_idx)

        if wall_orientation == "ver":
            self.state.ver[row_idx, col_idx] = 1
            self.state.ver[row_idx+1, col_idx] = 1

        if wall_orientation == "hor":
            self.state.hor[row_idx, col_idx] = 1
            self.state.hor[row_idx, col_idx+1] = 1

        self.state.walls[self.to_move] -= 1 #remove 1 wall of players resources


    def game_loop(self):
        while self.running:
            
            # Player 1
            self.to_move = self.s.P1
            move_ids, move_indices = self.get_all_legal_moves()
            p1_move = np.random.choice(move_ids)    #random for now
            self.use_move(p1_move)
            self.state.print_state()
            if self.check_win():
                break
            print(f"p1 picked move: {p1_move}")
            print(self._get_normal_moves()[0])
            # input()
            # End Player 1
            
            time.sleep(2)

            # Player 2 
            self.to_move = self.s.P2
            move_ids, move_indices = self.get_all_legal_moves()
            p2_move = np.random.choice(move_ids)    #random for now
            self.use_move(p2_move)
            self.state.print_state()
            if self.check_win():
                break
            time.sleep(2)
            # End Player 2

            # After turns
            self.turn += 1


#board example 5x5

#  - - - - -
# | | |X| | |
#  - - - - -
# | | | | | |
#  - - - - -
# | | | | | |
#  - - - - -
# | | | | | |
#  - - - - -
# | | |X| | |
#  - - - - -

"""
FIXED TODO urgent: when walls are nearby to strict so limited movement by player in acceptable moves
FIXED TODO urgent: wall moves can overlap?

TODO player to player collision
TODO validity of wall based on astar or anything
TODO special moves
TOOD update graph structure
"""

if __name__ == "__main__":
    game_env = QuoridorEnv()
    game_env.game_loop()
