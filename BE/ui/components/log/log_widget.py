from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QTextEdit, QSizePolicy
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from ...constants.styles import (FRAME_STYLE, CONTAINER_STYLE, LOG_TEXT_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import LOG_FRAME_WIDTH, LOG_CONTAINER_MIN_HEIGHT

class LogWidget(QFrame):
    """로그를 표시하는 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedWidth(LOG_FRAME_WIDTH)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 타이틀
        title = QLabel("로그 영역")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 로그 컨테이너
        container = QFrame()
        container.setStyleSheet(CONTAINER_STYLE)
        container.setMinimumSize(LOG_FRAME_WIDTH - 20, LOG_CONTAINER_MIN_HEIGHT)
        
        # 로그 컨테이너가 수직으로 늘어날 수 있도록 설정
        size_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        container.setSizePolicy(size_policy)
        
        # 로그 컨테이너 내부 레이아웃
        container_layout = QVBoxLayout()
        container.setLayout(container_layout)
        
        # 로그 출력을 위한 QTextEdit
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.log_text.setStyleSheet(LOG_TEXT_STYLE)
        
        # 로그 텍스트의 크기 정책을 Expanding으로 설정
        log_text_size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log_text.setSizePolicy(log_text_size_policy)
        
        container_layout.addWidget(self.log_text)
        layout.addWidget(container)
        
        self.setLayout(layout)
        
    def append(self, message):
        """로그 메시지 추가"""
        if message and message.strip():  # 빈 메시지가 아닌 경우에만 추가
            self.log_text.append(message.rstrip())  # 오른쪽 공백과 줄바꿈 제거
