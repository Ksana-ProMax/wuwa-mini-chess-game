from dataclasses import dataclass
from typing import Optional
from structure.board import Board


@dataclass
class State:
    parent: Optional["State"]
    board: Board
    depth: int
    children: list["State"]
    visited: bool = False