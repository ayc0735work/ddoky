from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel
from PySide6.QtCore import Qt, Signal
from BE.utils.key_handler import KeyboardHook, get_key_display_text, get_key_location, get_modifier_text

class KeyInputWidget(QWidget):
    """키 입력을 받고 표시하는 공통 위젯"""
    
    key_input_changed = Signal(dict)  # 키 입력이 변경되었을 때 발생하는 시그널
    
    def __init__(self, parent=None, show_details=True):
        super().__init__(parent)
        self.show_details = show_details  # 상세 정보 표시 여부
        self.last_key_info = None
        self.keyboard_hook = None
        self._setup_ui()
        
    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # 키 입력 표시
        self.key_display = QLineEdit()
        self.key_display.setReadOnly(True)
        self.key_display.setAlignment(Qt.AlignCenter)
        self.key_display.setPlaceholderText("여기를 클릭하고 키를 입력하세요")
        self.key_display.focusInEvent = self._on_focus_in
        self.key_display.focusOutEvent = self._on_focus_out
        layout.addWidget(self.key_display)
        
        if self.show_details:
            # 키 정보 레이블들
            self.key_code_label = QLabel("키 코드: ")
            self.scan_code_label = QLabel("스캔 코드 (하드웨어 고유값): ")
            self.virtual_key_label = QLabel("확장 가상 키 (운영체제 레벨의 고유 값): ")
            self.location_label = QLabel("키보드 위치: ")
            self.modifiers_label = QLabel("수정자 키: ")
            
            layout.addWidget(self.key_code_label)
            layout.addWidget(self.scan_code_label)
            layout.addWidget(self.virtual_key_label)
            layout.addWidget(self.location_label)
            layout.addWidget(self.modifiers_label)
        
        self.setLayout(layout)
        
    def _on_focus_in(self, event):
        """입력 박스가 포커스를 얻었을 때"""
        if not self.keyboard_hook:
            self.keyboard_hook = KeyboardHook()
            self.keyboard_hook.key_pressed.connect(self._on_key_pressed)
            self.keyboard_hook.start()
            
    def _on_focus_out(self, event):
        """입력 박스가 포커스를 잃었을 때"""
        if self.keyboard_hook:
            self.keyboard_hook.stop()
            self.keyboard_hook = None
            
    def _on_key_pressed(self, key_info):
        """키가 눌렸을 때"""
        # 이전 키 정보와 동일한 경우 무시
        if (self.last_key_info and 
            self.last_key_info['key_code'] == key_info['key_code'] and
            self.last_key_info['modifiers'] == key_info['modifiers'] and
            self.last_key_info['scan_code'] == key_info['scan_code']):
            return
            
        # 키 정보 업데이트
        self.last_key_info = key_info.copy()  # 딥 카피로 변경
        
        # 키 표시 텍스트 설정
        display_text = get_key_display_text(key_info)
        self.key_display.setText(display_text)
        
        if self.show_details:
            # 상세 정보 업데이트
            self.key_code_label.setText(f"키 코드: {key_info['key_code']}")
            self.scan_code_label.setText(f"스캔 코드: {key_info['scan_code']}")
            self.virtual_key_label.setText(f"가상 키: {key_info['virtual_key']}")
            self.location_label.setText(f"위치: {get_key_location(key_info['scan_code'])}")
            self.modifiers_label.setText(f"수정자 키: {get_modifier_text(key_info['modifiers'])}")
        
        # 키 정보 변경 시그널 발생
        self.key_input_changed.emit(key_info)
        
    def get_key_info(self):
        """현재 입력된 키 정보 반환"""
        return self.last_key_info
        
    def set_key_info(self, key_info):
        """키 정보 설정"""
        if not key_info:
            return
        
        self.last_key_info = key_info
        display_text = get_key_display_text(key_info)
        self.key_display.setText(display_text)
        
        if self.show_details:
            self.key_code_label.setText(f"키 코드: {key_info['key_code']}")
            self.scan_code_label.setText(f"스캔 코드: {key_info['scan_code']}")
            self.virtual_key_label.setText(f"가상 키: {key_info['virtual_key']}")
            self.location_label.setText(f"위치: {get_key_location(key_info['scan_code'])}")
            self.modifiers_label.setText(f"수정자 키: {get_modifier_text(key_info['modifiers'])}")

    def clear_key(self):
        """키 입력 초기화"""
        self.last_key_info = None
        self.key_display.clear()
        if self.show_details:
            self.key_code_label.setText("키 코드: ")
            self.scan_code_label.setText("스캔 코드: ")
            self.virtual_key_label.setText("가상 키: ")
            self.location_label.setText("위치: ")
            self.modifiers_label.setText("수정자 키: ")
        self.key_input_changed.emit({})
