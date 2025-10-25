from dataclasses import dataclass
from typing import Tuple, Dict, List

class Graph:
    def __init__(self, size: int):
        self.size = size
        self.graph: Dict[Tuple[int, int], Tuple[int, int]] = {}

    def construct_fc_graph(self):
        for y in range(self.size):
            for x in range(self.size):
                neighbors = []
                if y > 0:
                    neighbors.append((y - 1, x))
                if y < self.size - 1:
                    neighbors.append((y + 1, x))
                if x > 0:
                    neighbors.append((y, x - 1))
                if x < self.size - 1:
                    neighbors.append((y, x + 1))
                self.graph[(y, x)] = neighbors

    def is_edge(self, pos1, pos2) -> bool:
        if con_list := self.graph.get(pos1):
            if pos2 in con_list:
                return True
        return False

    def remove_connection(self, pos1:Tuple[int,int], pos2:Tuple[int,int]): 
        if con_list := self.graph.get(pos1):
            if pos2 in con_list:
                con_list.remove(pos2)

        if con_list := self.graph.get(pos2):
            if pos1 in con_list:
                con_list.remove(pos1) 



graph = Graph(5)
graph.construct_fc_graph()
graph.remove_connection((0,0), (1,0))
print(graph.graph)