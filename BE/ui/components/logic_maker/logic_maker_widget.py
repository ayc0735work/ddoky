from PySide6.QtWidgets import (QFrame, QVBoxLayout, QPushButton,
                             QLabel, QInputDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...constants.styles import (FRAME_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import LOGIC_MAKER_WIDTH, BASIC_SECTION_HEIGHT

class LogicMakerWidget(QFrame):
    """로직 메이커 위젯"""
    
    # 시그널 정의
    key_input = Signal(str)  # 키 입력이 추가되었을 때
    mouse_input = Signal(str)  # 마우스 입력이 추가되었을 때
    delay_input = Signal(str)  # 지연시간이 추가되었을 때
    record_mode = Signal(bool)  # 기록 모드가 토글되었을 때
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedSize(LOGIC_MAKER_WIDTH, BASIC_SECTION_HEIGHT)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 타이틀
        title = QLabel("로직 구성 메이커")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 버튼 레이아웃
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        
        # 키 입력 버튼
        self.key_btn = QPushButton("키 입력 추가")
        self.key_btn.setStyleSheet(BUTTON_STYLE)
        self.key_btn.clicked.connect(self._add_key_input)
        button_layout.addWidget(self.key_btn)
        
        # 마우스 입력 버튼
        self.mouse_btn = QPushButton("마우스 입력 추가")
        self.mouse_btn.setStyleSheet(BUTTON_STYLE)
        self.mouse_btn.clicked.connect(self._add_mouse_input)
        button_layout.addWidget(self.mouse_btn)
        
        # 지연시간 버튼
        self.delay_btn = QPushButton("지연시간 추가")
        self.delay_btn.setStyleSheet(BUTTON_STYLE)
        self.delay_btn.clicked.connect(self._add_delay)
        button_layout.addWidget(self.delay_btn)
        
        # 기록 모드 버튼
        self.record_btn = QPushButton("기록 모드")
        self.record_btn.setStyleSheet(BUTTON_STYLE)
        self.record_btn.setCheckable(True)
        self.record_btn.clicked.connect(self._toggle_record_mode)
        button_layout.addWidget(self.record_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def _add_key_input(self):
        """키 입력 추가"""
        key, ok = QInputDialog.getText(self, "키 입력", "입력할 키:")
        if ok and key:
            self.key_input.emit(f"키 입력: {key}")
            
    def _add_mouse_input(self):
        """마우스 입력 추가"""
        action, ok = QInputDialog.getText(self, "마우스 입력", "마우스 동작:")
        if ok and action:
            self.mouse_input.emit(f"마우스 입력: {action}")
            
    def _add_delay(self):
        """지연시간 추가"""
        delay, ok = QInputDialog.getInt(self, "지연시간", "지연시간(ms):", 1000, 0, 100000, 100)
        if ok:
            self.delay_input.emit(f"지연시간: {delay}ms")
            
    def _toggle_record_mode(self):
        """기록 모드 토글"""
        self.record_mode.emit(self.record_btn.isChecked())
