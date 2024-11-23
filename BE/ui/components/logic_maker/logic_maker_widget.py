from PySide6.QtWidgets import QFrame, QVBoxLayout, QPushButton, QLabel, QInputDialog
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...constants.styles import (FRAME_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import (LOGIC_MAKER_WIDTH, BASIC_SECTION_HEIGHT,
                                 MAKER_BUTTON_WIDTH)

class LogicMakerWidget(QFrame):
    """로직 생성을 위한 위젯"""
    
    # 시그널 정의
    key_input_requested = Signal()  # 키 입력 추가 요청
    mouse_input_requested = Signal()  # 마우스 입력 추가 요청
    delay_input_requested = Signal()  # 지연시간 추가 요청
    record_mode_toggled = Signal(bool)  # 기록 모드 토글 (True: 시작, False: 중지)
    logic_created = Signal(str)  # 새로운 로직이 생성되었을 때
    
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
        
        # 버튼 컨테이너
        button_container = QFrame()
        button_container.setStyleSheet(FRAME_STYLE)
        button_container_layout = QVBoxLayout()
        button_container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        button_container_layout.setSpacing(10)
        
        # 버튼 생성
        self.key_input_btn = QPushButton("키 입력 추가")
        self.mouse_input_btn = QPushButton("마우스 입력 추가")
        self.delay_btn = QPushButton("지연시간 추가")
        self.record_btn = QPushButton("기록 모드")
        
        # 버튼 설정 및 시그널 연결
        buttons = [
            (self.key_input_btn, self._handle_key_input),
            (self.mouse_input_btn, self._handle_mouse_input),
            (self.delay_btn, self._handle_delay_input),
            (self.record_btn, self._handle_record_mode)
        ]
        
        for btn, handler in buttons:
            btn.setFixedWidth(MAKER_BUTTON_WIDTH)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.clicked.connect(handler)
            button_container_layout.addWidget(btn)
            
        button_container.setLayout(button_container_layout)
        layout.addWidget(button_container, 1)  # stretch factor 1을 주어 남은 공간을 채우도록
        
        self.setLayout(layout)

    def _handle_key_input(self):
        """키 입력 추가 버튼 클릭 처리"""
        key, ok = QInputDialog.getText(self, "키 입력 추가", "추가할 키를 입력하세요:")
        if ok and key:
            self.key_input_requested.emit()
            self.logic_created.emit(f"{len(key)}개의 키 입력: {key}")
            
    def _handle_mouse_input(self):
        """마우스 입력 추가 버튼 클릭 처리"""
        options = ["클릭", "더블클릭", "우클릭", "드래그"]
        mouse_action, ok = QInputDialog.getItem(
            self, "마우스 입력 추가", "마우스 동작을 선택하세요:", options, 0, False
        )
        if ok and mouse_action:
            self.mouse_input_requested.emit()
            self.logic_created.emit(f"마우스 {mouse_action}")
            
    def _handle_delay_input(self):
        """지연시간 추가 버튼 클릭 처리"""
        delay, ok = QInputDialog.getInt(
            self, "지연시간 추가", "지연시간(ms)을 입력하세요:", 1000, 0, 10000, 100
        )
        if ok:
            self.delay_input_requested.emit()
            self.logic_created.emit(f"{delay}ms 지연")
            
    def _handle_record_mode(self):
        """기록 모드 버튼 클릭 처리"""
        self.record_btn.setChecked(not self.record_btn.isChecked())
        is_recording = self.record_btn.isChecked()
        self.record_btn.setText("기록 중지" if is_recording else "기록 모드")
        self.record_mode_toggled.emit(is_recording)
