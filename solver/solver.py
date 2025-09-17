"""
Brute force 寻找棋盘的最优解（最短步数）
"""

from collections import deque
from typing import Optional
import cv2
import numpy
from structure.board import Board
from structure.state import State


def minimum_steps_bfs(starting_board: numpy.ndarray):
    """BFS寻找最优解"""
    initial_board = Board.build_from_array(starting_board)
    if initial_board.is_complete():
        return 0, True

    queue: deque[tuple[Board, int]] = deque()
    queue.append((initial_board, 0))

    min_steps: int = 99999      # 最佳步数
    can_complete: bool = False  # 是否有解

    while True:
        if len(queue) == 0:
            break

        current_board, steps = queue.popleft()
        if steps >= min_steps:
            continue

        # 获取所有合法的操作
        actions = current_board.valid_actions()
        for block, shift in actions:
            new_board = current_board.take_action(block, shift)

            # 检查当前局面是否解决
            if new_board.is_complete():
                can_complete = True
                if steps + 1 < min_steps:
                    min_steps = steps + 1
                continue

            # 将新状态加入队列
            queue.append((new_board, steps + 1))
    return min_steps, can_complete


def minimum_steps_dfs(starting_board: numpy.ndarray):
    min_steps: int = 99999
    can_complete = False    # 是否有解
    best_node: Optional[State] = None
    initial_board = Board.build_from_array(starting_board)
    root = State(parent=None, board=initial_board,
                 depth=0, visited=False, children=[])
    cur: Optional[State] = root

    while True:
        # root 节点的 parent 为 None
        if cur is None:
            break

        cur.visited = True

        # 如果当前探索的层数已经超出了最佳层数，则直接返回上一级
        depth = cur.depth
        if depth >= min_steps:
            cur = cur.parent
            continue

        # 如果当前局面已经解决，返回上一级
        board = cur.board
        complete = board.is_complete()
        if complete:
            can_complete = True
            if depth < min_steps:
                min_steps = depth
                best_node = cur

            cur = cur.parent
            continue

        # 如果当前没有任何合法的操作，返回上一级
        actions = board.valid_actions_parallel()
        if len(actions) == 0:
            cur = cur.parent
            continue

        # 如果没有子节点，则构造子节点
        if len(cur.children) == 0:
            for (b, s) in actions:
                child_board = board.take_action(b, s)
                child_state = State(
                    parent=cur, board=child_board, depth=depth+1, visited=False, children=[])
                cur.children.append(child_state)

        # 如果当前所有子节点都被访问过了，则返回上一级
        all_visited = all([child.visited for child in cur.children])
        if all_visited:
            cur = cur.parent
            continue

        # 选择一个未被访问过的 children 并继续
        cur = next(child for child in cur.children if child.visited == False)
        continue

    # Debug
    if best_node is not None:
        cur = best_node
        index = min_steps
        while True:
            if cur is None:
                break

            cv2.imwrite(str(index)+".png", cur.board.visualization())
            cur = cur.parent
            index -= 1

    return min_steps, can_complete

