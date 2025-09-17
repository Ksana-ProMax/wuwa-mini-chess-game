from PyQt5.QtWidgets import QApplication
from app.app import WuwaBoardGameApp

if __name__ == "__main__":
    from preset import board_6_1
    
    app = QApplication([])
    window = WuwaBoardGameApp(board_6_1)
    window.show()
    app.exec_()