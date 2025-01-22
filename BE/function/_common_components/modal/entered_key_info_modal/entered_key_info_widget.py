from PySide6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel
from PySide6.QtCore import Qt, Signal

class EnteredKeyInfoWidget(QWidget):
    """키 입력을 표시하는 UI 위젯
    
    이 위젯은 순수하게 UI 표시만을 담당합니다:
    1. 키 입력 상태를 시각적으로 표시
    2. 포커스 상태 변경을 시그널로 알림
    3. 상세 정보 표시 여부 설정
    """
    
    key_input_area_focused = Signal()    # 키 입력 영역이 포커스를 얻었을 때
    key_input_area_unfocused = Signal()  # 키 입력 영역이 포커스를 잃었을 때
    log_message = Signal(str)  # 로그 메시지 시그널 정의
    
    def __init__(self, parent=None, show_details=True):
        """EnteredKeyInfoWidget 초기화
        
        Args:
            parent (QWidget, optional): 부모 위젯
            show_details (bool): 키 입력 상세 정보 표시 여부
        """
        super().__init__(parent)
        self.show_details = show_details
        self._setup_ui()
    
    def _setup_ui(self):
        """UI 컴포넌트 초기화 및 배치"""
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
        """입력 박스가 포커스를 얻었을 때 시그널 발생"""
        self.key_input_area_focused.emit()
    
    def _on_focus_out(self, event):
        """입력 박스가 포커스를 잃었을 때 시그널 발생"""
        self.key_input_area_unfocused.emit()
    
    def update_key_info(self, formatted_key_info):
        """구조화된 키 정보로 UI를 업데이트합니다.
        
        Args:
            formatted_key_info (dict): 구조화된 키 정보
        """
        if not formatted_key_info:
            return
            
        # 메인 키 표시
        self.key_display.setText(formatted_key_info['simple_display_text'])
        
        # 상세 정보 표시
        if self.show_details:
            self.key_code_label.setText(f"키 코드: {formatted_key_info['key_code']}")
            self.scan_code_label.setText(f"스캔 코드: {formatted_key_info['scan_code']}")
            self.virtual_key_label.setText(f"가상 키: {formatted_key_info['virtual_key']}")
            self.location_label.setText(f"위치: {formatted_key_info['location']}")
            self.modifiers_label.setText(f"수정자 키: {formatted_key_info['modifier_text']}")
    
    def clear_key(self):
        """키 입력 표시를 초기화합니다."""
        self.key_display.clear()
        if self.show_details:
            self.key_code_label.setText("키 코드: ")
            self.scan_code_label.setText("스캔 코드: ")
            self.virtual_key_label.setText("가상 키: ")
            self.location_label.setText("위치: ")
            self.modifiers_label.setText("수정자 키: ")
