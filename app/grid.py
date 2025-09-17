from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import QSize, Qt
from structure.data_type import Point

class GridButton(QPushButton):
    def __init__(self, position: Point, size: int = 60, parent=None):
        super().__init__("", parent)
        self.coord = position
        self.setFixedSize(QSize(size, size))
        
    def set_block_style(self, color_code: str, is_active: bool):
        if is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color_code};
                    border: 3px solid black;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color_code};
                    border: 3px solid gray;
                }}
            """)
        self.setEnabled(is_active)
        
    def set_empty_style(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: lightgray;
                border: 1px solid darkgray;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 2px solid darkgray;
            }
        """)
        self.setEnabled(True)
        
    def set_invalid_style(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: black;
                border: none;
            }
        """)
        self.setEnabled(False)