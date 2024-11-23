from PySide6.QtWidgets import (QFrame, QVBoxLayout, QPushButton,
                             QLabel, QInputDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...constants.styles import (FRAME_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import LOGIC_MAKER_WIDTH, BASIC_SECTION_HEIGHT
from .key_input_dialog import KeyInputDialog

class LogicMakerWidget(QFrame):
    """로직 메이커 위젯"""
    
    # 시그널 정의
    key_input = Signal(dict)  # 키 입력이 추가되었을 때 (키 정보를 딕셔너리로 전달)
    mouse_input = Signal(str)  # 마우스 입력이 추가되었을 때
    delay_input = Signal(str)  # 지연시간이 추가되었을 때
    record_mode = Signal(bool)  # 기록 모드가 토글되었을 때
    log_message = Signal(str)  # 로그 메시지를 전달하는 시그널
    
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
        dialog = KeyInputDialog(self)
        dialog.key_selected.connect(self._on_key_selected)
        dialog.exec()
        
    def _on_key_selected(self, key_info):
        """키가 선택되었을 때 호출"""
        # 로그 메시지 생성
        key_text = key_info['text'] if key_info['text'] else f"Key_{key_info['key']}"
        log_msg = (f"키 입력이 추가되었습니다 [ "
                  f"키: {key_text}, "
                  f"스캔 코드: {key_info['scan_code']}, "
                  f"가상 키: {key_info['virtual_key']}, "
                  f"키보드 위치: {self._get_key_location(key_info['scan_code'])}, "
                  f"수정자 키: {self._get_modifier_text(key_info['modifiers'])} ]")
        
        # 로그 메시지 전달
        self.log_message.emit(log_msg)
        
        # 키 정보 전달
        self.key_input.emit(key_info)
            
    def _get_key_location(self, scan_code):
        """키의 키보드 위치 정보 반환"""
        if scan_code in [42, 29, 56]:  # 왼쪽 Shift, Ctrl, Alt
            return "키보드 왼쪽"
        elif scan_code in [54, 285, 312]:  # 오른쪽 Shift, Ctrl, Alt
            return "키보드 오른쪽"
        elif 71 <= scan_code <= 83:  # 숫자패드 영역
            return "숫자패드"
        return "메인 키보드"
        
    def _get_modifier_text(self, modifiers):
        """수정자 키 텍스트 생성"""
        mod_texts = []
        
        if modifiers & Qt.ShiftModifier:
            mod_texts.append("Shift")
        if modifiers & Qt.ControlModifier:
            mod_texts.append("Ctrl")
        if modifiers & Qt.AltModifier:
            mod_texts.append("Alt")
            
        return " + ".join(mod_texts) if mod_texts else "없음"
            
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
