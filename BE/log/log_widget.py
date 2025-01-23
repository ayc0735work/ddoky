from PySide6.QtWidgets import (QFrame, QVBoxLayout, QLabel, QTextEdit, 
                              QSizePolicy, QHBoxLayout, QPushButton)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from BE.function.constants.styles import (FRAME_STYLE, CONTAINER_STYLE, LOG_TEXT_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from BE.function.constants.dimensions import LOG_FRAME_WIDTH, LOG_CONTAINER_MIN_HEIGHT
from BE.log.manager.base_log_manager import BaseLogManager

class LogWidget(QFrame):
    """로그를 표시하는 위젯"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        # BaseLogManager에 핸들러로 등록
        BaseLogManager.instance().add_handler(self.append)
        
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
        
        # 로그 기능 버튼 영역
        button_layout = QHBoxLayout()
        
        # 초기화 버튼
        clear_btn = QPushButton("초기화")
        clear_btn.clicked.connect(self.clear_log)
        button_layout.addWidget(clear_btn)
        
        # 맨 위로 버튼
        scroll_top_btn = QPushButton("맨 위로")
        scroll_top_btn.clicked.connect(self.scroll_to_top)
        button_layout.addWidget(scroll_top_btn)
        
        # 맨 아래로 버튼
        scroll_bottom_btn = QPushButton("맨 아래로")
        scroll_bottom_btn.clicked.connect(self.scroll_to_bottom)
        button_layout.addWidget(scroll_bottom_btn)
        
        button_layout.addStretch()  # 남은 공간을 채움
        layout.addLayout(button_layout)
        
        # 로그 박스
        log_box = QFrame()
        log_box.setStyleSheet(CONTAINER_STYLE)
        log_box.setMinimumSize(LOG_FRAME_WIDTH - 20, LOG_CONTAINER_MIN_HEIGHT)
        
        # 로그 박스가 수직으로 늘어날 수 있도록 설정
        size_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        log_box.setSizePolicy(size_policy)
        
        # 로그 박스 내부 레이아웃
        log_box_layout = QVBoxLayout()
        log_box.setLayout(log_box_layout)
        
        # 로그 출력을 위한 QTextEdit
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.log_text.setStyleSheet(LOG_TEXT_STYLE)
        self.log_text.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse | 
            Qt.TextInteractionFlag.TextSelectableByKeyboard
        )
        # HTML 지원 활성화
        self.log_text.setAcceptRichText(True)
        
        # 로그 텍스트의 크기 정책을 Expanding으로 설정
        log_text_size_policy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.log_text.setSizePolicy(log_text_size_policy)
        
        log_box_layout.addWidget(self.log_text)
        layout.addWidget(log_box)
        
        self.setLayout(layout)
        
    def append(self, message):
        """로그 메시지 추가"""
        if message and message.strip():  # 빈 메시지가 아닌 경우에만 추가
            self.log_text.append(message.rstrip())  # 오른쪽 공백과 줄바꿈 제거
            
    def clear_log(self):
        """로그 메시지 초기화"""
        self.log_text.clear()
        
    def scroll_to_top(self):
        """로그 맨 위로 스크롤"""
        self.log_text.verticalScrollBar().setValue(0)
        
    def scroll_to_bottom(self):
        """로그 맨 아래로 스크롤"""
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )
