from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...constants.styles import (FRAME_STYLE, CONTAINER_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import ADVANCED_FRAME_WIDTH, ADVANCED_SECTION_HEIGHT

class AdvancedWidget(QFrame):
    """고급 기능을 위한 위젯"""
    
    # 시그널 정의
    advanced_action = Signal(str)  # 고급 기능 액션이 발생했을 때
    log_message = Signal(str)  # 로그 메시지 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedWidth(ADVANCED_FRAME_WIDTH)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 타이틀
        title = QLabel("고급 기능 영역")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 고급 기능 컨테이너
        container = QFrame()
        container.setStyleSheet(CONTAINER_STYLE)
        container.setFixedSize(ADVANCED_FRAME_WIDTH - 20, ADVANCED_SECTION_HEIGHT)
        layout.addWidget(container)
        
        self.setLayout(layout)
