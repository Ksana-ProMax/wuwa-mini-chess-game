from random import shuffle
from typing import Optional
from PyQt5.QtWidgets import  QMainWindow, QLabel, QWidget, QGridLayout, QPushButton, QAction, QMessageBox
from PyQt5.QtCore import Qt, QSize
import numpy
from app.grid import GridButton
from structure.block import Block
from structure.board import Board
from solver.solver import minimum_steps_bfs
from PIL import ImageColor

from structure.data_type import Point

class WuwaBoardGameApp(QMainWindow):
    COLOR_MAP = [code for _, code in ImageColor.colormap.items()]
    shuffle(COLOR_MAP)

    def __init__(self, board: numpy.ndarray):
        super().__init__()
        self.init_board = board
        self.setWindowTitle("鸣潮-兽痕解析")
        self.resize(1280, 720)

        # 利用 solver 找出最佳步数
        self.optimal_steps, _ = minimum_steps_bfs(self.init_board)
        self.remaining_steps = self.optimal_steps
        self.board = Board.build_from_array(self.init_board)

        self.selected_coord: Optional[Point] = None
        self.selected_block: Optional[Block] = None
        self.valid_actions: list = []
        self.buttons = {}
        self.build_gui()

    def build_gui(self):
        # 在画面右上角构造一个 QLabel 显示剩余步数，初始值为 optimal_steps
        self.steps_label = QLabel(f"剩余步数: {self.remaining_steps}", self)
        self.steps_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        # 构造 H * W 排列的按钮组
        # board 里面 grid_mask 为 -1 的地方，不生成按钮
        # 设置按钮的颜色为棋子的颜色
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QGridLayout(central_widget)
        layout.setSpacing(2)

        height, width = self.board.shape
        for i in range(height):
            for j in range(width):
                button = GridButton((i, j), parent=self)

                # grid_mask 为 -1 的地方
                if self.board.grid_mask[i, j] == False:
                    button.set_invalid_style()
                else:
                    # 设置按钮的颜色为棋子的颜色
                    block = self.board.find_block_by_coord((i, j))
                    if block:
                        color_code = self.COLOR_MAP[(block.color - 1) % len(self.COLOR_MAP)]
                        if not isinstance(color_code, str):
                            raise Exception("color code 需要是 str 形式")
                        button.set_block_style(color_code, block.active)
                    else:
                        button.set_empty_style()

                    # 添加点击按钮事件
                    button.clicked.connect(self.on_button_clicked)
                    
                layout.addWidget(button, i, j)
                self.buttons[(i, j)] = button
        
        # 添加重置按钮
        open_action = QAction("重置游戏", self)
        open_action.triggered.connect(self.reset_game)
        menubar = self.menuBar()
        file_menu = menubar.addMenu("游戏")
        file_menu.addAction(open_action)
         
    def on_button_clicked(self):
        button = self.sender()
        if not isinstance(button, GridButton):
            return
            
        coord = button.coord

        if self.selected_block is None:
            # 如果选择的按钮上面有棋子，则获取这个按钮对应的棋子的区块
            # 计算并缓存对应的 valid_actions
            block = self.board.find_block_by_coord(coord)
            if block and block.active:
                self.selected_coord = coord
                self.selected_block = block
                self.valid_actions = self.board.valid_actions_by_block(block)
                print("block: ", self.selected_block, "actions: ", self.valid_actions)
            else:
                print("选择的地方没有区块或区块不可移动")
        else:                 
            # 如果已经选择了区块，尝试移动
            self.try_move_block(coord)

            self.selected_coord = None
            self.selected_block = None
            self.valid_actions = []
            print("所有选择已重置")

    def refresh(self):
        """刷新UI"""
        return
    
    def try_move_block(self, target_position):
        block = self.selected_block
        coord = self.selected_coord

        if block is None or coord is None:
            return
        
        # 计算偏移量
        shift_x, shift_y = target_position[0] - coord[0], target_position[1] - coord[1]
        if (block, (shift_x, shift_y)) in self.valid_actions:
            print("合法操作")
            self.board = self.board.take_action(block, (shift_x, shift_y))
            self.remaining_steps -= 1
            if self.board.is_complete():
                QMessageBox.information(self, "消息", "游戏完成")
            else:
                valid_actions = self.board.valid_actions()
                if len(valid_actions) == 0:
                    QMessageBox.information(self, "消息", "游戏失败, 没有地方可以行动, 请重置游戏")

            self.refresh()

    def refresh(self):
        """刷新UI"""
        height, width = self.board.shape
        for i in range(height):
            for j in range(width):
                if self.board.grid_mask[i, j] == 0:
                    continue
                    
                button = self.buttons[(i, j)]
                block = self.board.find_block_by_coord((i, j))
                
                if block:
                    color_code = self.COLOR_MAP[(block.color - 1) % len(self.COLOR_MAP)]
                    button.set_block_style(color_code, block.active)
                else:
                    button.set_empty_style()

    def reset_game(self):
        """重置游戏状态"""
        self.remaining_steps = self.optimal_steps
        self.board = Board.build_from_array(self.init_board)
        self.selected_block = None
        self.refresh()