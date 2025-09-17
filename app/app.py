from random import randint
from typing import Optional
from PyQt5.QtWidgets import  QMainWindow, QLabel, QWidget, QGridLayout, QPushButton, QAction
from PyQt5.QtCore import Qt, QSize
import numpy
from structure.block import Block
from structure.board import Board
from solver.solver import minimum_steps_bfs
from PIL import ImageColor

class WuwaBoardGameApp(QMainWindow):
    COLOR_MAP = [code for _, code in ImageColor.colormap.items()]
    COLOR_MAP.sort(key=lambda x: randint(-20, 20))

    def __init__(self, board: numpy.ndarray):
        super().__init__()
        self.init_board = board
        self.setWindowTitle("鸣潮-兽痕解析")
        self.resize(1280, 720)

        # 利用 solver 找出最佳步数
        self.optimal_steps, _ = minimum_steps_bfs(self.init_board)
        self.remaining_steps = self.optimal_steps
        self.board = Board.build_from_array(self.init_board)

        self.selected_block: Optional[Block] = None
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

        # 如果按钮对应的 block 为 active 那么这个按钮可以被点击；否则这个按钮不能被点击
        height, width = self.board.shape
        grid_size = 60 
        for i in range(height):
            for j in range(width):
                # board 里面 grid_mask 为 -1 的地方，不生成按钮
                if self.board.grid_mask[i, j] == 0:
                    _button_ = QPushButton("", self)
                    _button_.setFixedSize(QSize(grid_size, grid_size))
                    _button_.setEnabled(False)
                    _button_.setStyleSheet("background-color: black; border: none;")
                    layout.addWidget(_button_, i, j)
                else:
                    # 创建按钮
                    button = QPushButton("", self)
                    button.setFixedSize(QSize(grid_size, grid_size))
                    button.setProperty("position", (i, j))
                    
                    # 设置按钮的颜色为棋子的颜色
                    block = self.board.find_block_by_coord((i, j))
                    if block:
                        # 如果区块是活跃的，添加边框
                        if block.active:
                            color_code = self.COLOR_MAP[(block.color - 1) % 6]
                            button.setStyleSheet(f"""
                                QPushButton {{
                                    background-color: {color_code};
                                    border: 8px solid black;
                                }}
                            """)
                        else:
                            button.setStyleSheet("border: 1px")
                        
                        # 点击事件
                        button.clicked.connect(self.on_button_clicked)
                    else:
                        button.setStyleSheet("border: 1px")
                        button.setEnabled(False)
                    
                    layout.addWidget(button, i, j)
        
        # 添加重置按钮
        open_action = QAction("重置游戏", self)
        open_action.triggered.connect(self.reset_game)
        menubar = self.menuBar()
        file_menu = menubar.addMenu("游戏")
        file_menu.addAction(open_action)
         
    def on_button_clicked(self):
        return 
    
    def refresh(self):
        """"""
        return

    def reset_game(self):
        """重置游戏状态"""
        self.remaining_steps = self.optimal_steps
        self.board = Board.build_from_array(self.init_board)
        self.selected_block = None
        self.refresh()