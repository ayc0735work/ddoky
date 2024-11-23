from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QFont

from ...constants.styles import TITLE_FONT_FAMILY, TITLE_FONT_SIZE

class TitleWidget(QLabel):
    """애플리케이션 타이틀 위젯"""
    
    def __init__(self, parent=None):
        super().__init__("또키 - 종합 매크로", parent)
        self.init_font()
        
    def init_font(self):
        """타이틀 폰트 설정"""
        font = QFont(TITLE_FONT_FAMILY, TITLE_FONT_SIZE, QFont.Weight.Bold)
        self.setFont(font)
