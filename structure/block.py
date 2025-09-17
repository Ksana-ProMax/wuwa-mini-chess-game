from typing import Self
from structure.data_type import Point

class Block:
    def __init__(self, pieces: list[Point], color: int, active: bool) -> None:
        self.pieces: list[Point] = pieces
        """这个区块下面的所有节点/棋子"""
        self.color: int = color
        """这个区块的颜色"""
        self.active: bool = active
    
    def merge(self, target: Self):
        """合并对方的节点到自己的节点下面"""
        self.pieces += target.pieces