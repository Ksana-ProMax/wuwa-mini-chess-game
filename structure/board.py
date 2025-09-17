from concurrent.futures import ThreadPoolExecutor
from random import shuffle
from typing import Optional, Self
import cv2
import numpy
from collections import deque
from structure.block import Block
from structure.data_type import Point
from PIL import ImageColor

COLORS = [ImageColor.getrgb(code) for _, code in ImageColor.colormap.items()]
shuffle(COLORS)

class Board:
    def __init__(self, blocks: list[Block], grid_mask: numpy.ndarray) -> None:
        self.grid_mask = numpy.array(grid_mask)
        """生成一个棋盘自身是否可以放置棋子的遮罩, 0代表不能放置, 1代表可以放置"""
        self.shape: tuple = grid_mask.shape # 棋盘的长和宽
        self.size: int = grid_mask.size
        self.action_space: int = self.size * self.size
        self.blocks: list[Block] = blocks

    def valid_actions(self) -> list[tuple[Block, Point]]:
        """
        给出当前状态下, 所有合法的操作
        合法的操作满足以下条件：
            1. 被移动的区块active必须为True
            2. 被移动的区块, 只能移动到和同色 block 邻接的位置 (上下左右四个方向) 
            3. 区块移动后, 区块下的所有的节点不能越界, 不能与 grid_mask 为 False 的地方有重叠, 不能与其他棋子有重叠
        
        Returns
        -------
        所有合法操作 (block, shift) 的列表, 
        block代表了被移动的区块, shift代表了区块平移的距离(x, y)

        Example
        -------
        一个 2*4 的棋盘, 棋子的配置为
        1,1,0,0
        0,0,2,1
        则其中可以移动的只有颜色为1的区块, 颜色为2的区块没有其他颜色2区块可以邻接, 
        并且颜色为1的区块只能移动到另外一个颜色为1的区块的相邻位置；
        所以可以移动的方式有4种：
        1,1,0,0
        1,0,2,0

        1,1,0,0
        0,1,2,0

        1,1,1,0
        0,0,2,0

        0,0,1,1
        0,0,2,1
        """
        actions = []
        active_blocks = [block for block in self.blocks if block.active]

        for block in active_blocks:
            actions += self.valid_actions_by_block(block)
            
        return actions

    def valid_actions_parallel(self, workers=8) -> list[tuple[Block, Point]]:
        """
        valid_actions的多线程版本, 不推荐使用, 运行速度会比非多线程的版本慢
        """
        actions = []
        active_blocks = [block for block in self.blocks if block.active]

        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = executor.map(self.valid_actions_by_block, active_blocks)
            for actions_for_block in results:
                actions += actions_for_block

        return actions
    
    def valid_actions_by_block(self, block: Block) -> list[tuple[Block, Point]]:
        """
        找到单个区块所有合法的操作
        """
        same_color_blocks = [b for b in self.blocks if b.color == block.color and b is not block]
        if not same_color_blocks:
            return []   # 没有其他同色区块可以拼接

        actions = []

        other_blocks = [b for b in self.blocks if b is not block]
        piece_mask = self.build_piece_mask(other_blocks)

        # 去重，例如 A,B,C 三个区块拼接时, A-B 的合法动作和 A-C的合法动作是同一个
        seen_shifts = set() 

        # 找到所有的同色区块，以及这些区块相邻的位置
        for other_block in same_color_blocks:
            other_block_pieces = other_block.pieces
            # 获取区块下面的每一个棋子，并且找出其相邻的位置
            for other_piece in other_block_pieces:
                for dx, dy in ((-1, 0), (0, 1), (1, 0), (0, -1)):
                    adj_pos = (other_piece[0] + dx, other_piece[1] + dy)

                    if not (0 <= adj_pos[0] < self.shape[0] and 0 <= adj_pos[1] < self.shape[1]):
                        continue    # 不在边界内

                    if (not piece_mask[adj_pos] or not self.grid_mask[adj_pos]):
                        continue    # 相邻的位置不可部署

                    for piece in block.pieces:
                        # 计算区块的偏移量
                        shift_x = adj_pos[0] - piece[0]
                        shift_y = adj_pos[1] - piece[1]

                        if (shift_x, shift_y) in seen_shifts:
                            continue 

                        if (shift_x == 0 and shift_y == 0):
                            continue    # 原地不动，正常逻辑不会出现这个区块

                        valid_move = True
                        for p in block.pieces:
                            new_x, new_y = p[0] + shift_x, p[1] + shift_y

                            # 保证区块整体移动时，所有的棋子都部署在合法的区域上面
                            if not (0 <= new_x < self.shape[0] and 0 <= new_y < self.shape[1]):
                                valid_move = False  
                                break

                            if (not self.grid_mask[new_x, new_y]) or (not piece_mask[new_x, new_y]):
                                valid_move = False
                                break

                        if valid_move:
                            seen_shifts.add((shift_x, shift_y))
                            actions.append((block, (shift_x, shift_y)))
        return actions
    
    def build_piece_mask(self, blocks: list[Block]) -> numpy.ndarray:
        """
        根据当前的棋子的部署, 生成一个当前棋盘棋子占用的遮罩
        False 代表这个区域被棋子占用
        True 代表这个区域未被棋子占用, 可以部署棋子在上面
        """
        mask = numpy.full(self.shape, fill_value=True, dtype=bool)
        for block in blocks:
            for x, y in block.pieces:
                mask[x, y] = False
        return mask

    def is_complete(self) -> bool:
        """
        检验当前游戏状态是否为结束状态
        结束状态的要求：
            1. blocks 里面没有重复颜色的区块, 
            2. blocks 里面所有的区块, active 状态都为 True
        """
        color_set = set()
        for block in self.blocks:
            if block.color in color_set:
                return False
            color_set.add(block.color)

        for block in self.blocks:
            if not block.active:
                return False
            
        return True

    def take_action(self, block: Block, shift: tuple[int, int]) -> "Board":
        """
        执行动作, 将 block 平移 shift 的位置后, 移动到指定的地方, 
        移动之后, 合并相邻的相同颜色的区块, 并将 active 设置为 True
        并且, 其他所有同色的区块, active 设置为 False

        Return
        ------
        执行动作之后的新的 Board
        """
        new_blocks = []
        for b in self.blocks:
            new_pieces = list(b.pieces)  # 复制
            new_blocks.append(Block(new_pieces, b.color, b.active))
        
        target_block = new_blocks[self.blocks.index(block)]
        
        if target_block is None:
            return self
        
        dx, dy = shift
        
        # 移动区块的棋子
        new_pieces = []
        for piece in target_block.pieces:
            x, y = piece
            new_x, new_y = x + dx, y + dy
            new_pieces.append((new_x, new_y))
            
        target_block.pieces = new_pieces
        
        # 合并相邻的同色区块
        blocks_to_merge = []
        for block in new_blocks:
            if block is target_block or block.color != target_block.color:
                continue
                
            # 检查区块是否相邻
            for piece in target_block.pieces:
                for other_piece in block.pieces:
                    if (abs(piece[0] - other_piece[0]) + abs(piece[1] - other_piece[1])) == 1:
                        blocks_to_merge.append(block)
                        break
                if block in blocks_to_merge:
                    break
        
        for block in blocks_to_merge:
            target_block.merge(block)
            new_blocks.remove(block)
            
        # 更新区块的 active, 同色区块 active 为 False, 只保留 target_block 的 active 为 True
        for block in new_blocks:
            if block.color == target_block.color:
                block.active = False
        target_block.active = True

        # 创建并返回新的 Board 实例
        new_board = Board(new_blocks, self.grid_mask.copy())
        return new_board

    def find_block_by_coord(self, coord: Point) -> Optional[Block]:
        target_block = None
        for block in self.blocks:
            piece_coords = block.pieces
            if coord in piece_coords:
                target_block = block
                break
        return target_block
    
    @staticmethod
    def build_grid_mask(board: numpy.ndarray) -> numpy.ndarray:
        mask = numpy.full(board.shape, fill_value=True, dtype=bool)
        mask[board < 0] = False
        return mask

    @staticmethod
    def build_blocks(board: numpy.ndarray) -> list[Block]:
        """
        计算所有相互连接的区块
        """
        results: list[Block] = []
        visited = numpy.zeros(board.shape, dtype=bool)
        
        for row in range(board.shape[0]):
            for col in range(board.shape[1]):
                if visited[row, col] or board[row, col] <= 0:
                    continue
                    
                connected_pieces = Board.get_connected_pieces(board, (row, col))
                color = board[row, col]
                new_block = Block(connected_pieces, color, True)
                results.append(new_block)
                
                for r, c in connected_pieces:
                    visited[r, c] = True
        return results


    @staticmethod
    def get_connected_pieces(board: numpy.ndarray, coord: Point) -> list[Point]:
        """
        获取与指定的坐标 coord 相连接的颜色相同的所有棋子

        Example
        -------
        棋盘的设定为：
            1,2,1,1
            1,1,1,0
        如果 coord 为 (0,0), 
        则返回坐标为 (0,0) 的棋子, 相连接的同色 (1) 的所有棋子, 对应的坐标位置的列表：
            [(0,0), (0,2), (0,3), (1,0), (1,1), (1,2)]
        """
        row, col = coord
        if (row < 0 or row >= board.shape[0] or col < 0 or col >= board.shape[1]):
            return []
        color = board[row, col]
        if color <= 0:
            return []
        
        visited = set()
        connected: list[Point] = []
        queue = deque([(row, col)])
        
        directions: list[Point] = [(-1, 0), (0, 1), (1, 0), (0, -1)] # 上、右、下、左
        while queue:
            r, c = queue.popleft()
            if (r, c) in visited:
                continue
                
            visited.add((r, c))
            connected.append((r, c))
            
            # 检查四个方向
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                # 检查坐标是否在棋盘范围内
                if (0 <= nr < board.shape[0] and 0 <= nc < board.shape[1] and 
                    (nr, nc) not in visited and board[nr, nc] == color):
                    queue.append((nr, nc))
        
        return connected
    
    def visualization(self, grid_size: int = 50):
        """
        可视化
        ------
        生成一个 height 为 (长*grid_size), width 为 (宽*grid_size) 的图片
        图片中, grid_mask 为 False 的区域为黑色, True 的地方为白色
        有棋子的地方, 用圆圈代表棋子, 并且圆圈的颜色代表棋子的颜色
        """
        # 创建空白图像
        height, width = self.shape
        img = numpy.ones((height * grid_size, width * grid_size, 3), dtype=numpy.uint8) * 255
            
        # 绘制网格遮罩
        for i in range(height):
            for j in range(width):
                if not self.grid_mask[i, j]:
                    # 不可放置区域, 绘制为黑色
                    cv2.rectangle(img, 
                                (j * grid_size, i * grid_size),
                                ((j + 1) * grid_size, (i + 1) * grid_size),
                                (0, 0, 0), -1)
                else:
                    # 可放置区域, 绘制为白色 (已经是白色, 只需绘制网格线) 
                    cv2.rectangle(img,
                                (j * grid_size, i * grid_size),
                                ((j + 1) * grid_size, (i + 1) * grid_size),
                                (200, 200, 200), 1)
                    
        # 绘制连线
        for block in self.blocks:
            for piece in block.pieces:
                x, y = piece
                center = (y * grid_size + grid_size // 2, x * grid_size + grid_size // 2)
                
                # 上、右、下、左四个方向
                for dx, dy in [(-1, 0), (0, 1), (1, 0), (0, -1)]:
                    nx, ny = x + dx, y + dy
                    if (nx, ny) in block.pieces:
                        # 找到相邻棋子，绘制灰色的线段
                        neighbor_center = (ny * grid_size + grid_size // 2, nx * grid_size + grid_size // 2)
                        cv2.line(img, center, neighbor_center, (80, 80, 80), 4)

        # 绘制棋子
        for block in self.blocks:
            color = COLORS[block.color % len(COLORS)]
            for piece in block.pieces:
                x, y = piece
                center = (y * grid_size + grid_size // 2, x * grid_size + grid_size // 2)
                radius = grid_size // 3
                
                cv2.circle(img, center, radius, color, -1)
                
                # 如果区块是活跃的, 绘制外框
                if block.active:
                    cv2.circle(img, center, radius + 2, (0, 0, 0), 2)
        return img

    @classmethod
    def build_from_array(cls, arr: numpy.ndarray):
        blocks = cls.build_blocks(arr)
        if len(blocks) == 0:
            raise Exception("len(blocks) == 0 棋盘不是合法的棋盘")
        
        mask = cls.build_grid_mask(arr)
        return cls(blocks, mask)
    