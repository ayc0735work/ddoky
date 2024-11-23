from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent

class KeyInputDialog(QDialog):
    """키 입력을 받는 다이얼로그"""
    
    key_selected = Signal(dict)  # 선택된 키 정보를 전달하는 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("키 입력")
        self.setFixedSize(400, 300)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        
        self.last_key_info = None  # 마지막으로 입력된 키 정보
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 안내 메시지
        guide_label = QLabel("입력하려는 키를 누르세요")
        guide_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(guide_label)
        
        # 입력된 키 표시
        self.key_display = QLineEdit()
        self.key_display.setReadOnly(True)
        self.key_display.setAlignment(Qt.AlignCenter)
        self.key_display.setPlaceholderText("키를 입력하세요")
        layout.addWidget(self.key_display)
        
        # 키 정보 프레임
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.StyledPanel)
        info_layout = QVBoxLayout()
        
        # 키 정보 레이블들
        self.key_code_label = QLabel("키 코드: ")
        self.scan_code_label = QLabel("스캔 코드: ")
        self.virtual_key_label = QLabel("가상 키: ")
        self.location_label = QLabel("키보드 위치: ")
        self.modifiers_label = QLabel("수정자 키: ")
        
        info_layout.addWidget(self.key_code_label)
        info_layout.addWidget(self.scan_code_label)
        info_layout.addWidget(self.virtual_key_label)
        info_layout.addWidget(self.location_label)
        info_layout.addWidget(self.modifiers_label)
        
        info_frame.setLayout(info_layout)
        layout.addWidget(info_frame)
        
        # 버튼 영역
        button_layout = QHBoxLayout()
        save_button = QPushButton("저장")
        cancel_button = QPushButton("취소")
        
        save_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def keyPressEvent(self, event: QKeyEvent):
        """키 입력 이벤트 처리"""
        # Esc 키는 다이얼로그를 닫는데 사용
        if event.key() == Qt.Key_Escape:
            self.reject()
            return
            
        # 키 정보 저장
        self.last_key_info = {
            'key': event.key(),
            'scan_code': event.nativeScanCode(),
            'virtual_key': event.nativeVirtualKey(),
            'text': event.text(),
            'modifiers': event.modifiers()
        }
        
        # 키 정보 표시 업데이트
        self._update_key_info()
        
    def _update_key_info(self):
        """키 정보 표시 업데이트"""
        if not self.last_key_info:
            return
            
        # 키 표시 텍스트 설정
        key_text = self._get_key_display_text()
        self.key_display.setText(key_text)
        
        # 키 정보 레이블 업데이트
        self.key_code_label.setText(f"키 코드: {self.last_key_info['key']}")
        self.scan_code_label.setText(f"스캔 코드: {self.last_key_info['scan_code']}")
        self.virtual_key_label.setText(f"가상 키: {self.last_key_info['virtual_key']}")
        
        # 위치 정보 (스캔 코드 기반으로 판단)
        location = self._get_key_location()
        self.location_label.setText(f"위치: {location}")
        
        # 수정자 키 정보
        modifiers = self._get_modifier_text()
        self.modifiers_label.setText(f"수정자 키: {modifiers}")
        
    def _get_key_display_text(self):
        """키 표시 텍스트 생성"""
        key = self.last_key_info['key']
        text = self.last_key_info['text']
        location = self._get_key_location()
        
        if text:
            return f"{text} ({location})"
        return f"Key_{key} ({location})"
        
    def _get_key_location(self):
        """키의 위치 정보 반환"""
        scan_code = self.last_key_info['scan_code']
        
        # 예시적인 위치 판단 (실제 구현 시 더 자세한 매핑 필요)
        if scan_code in [42, 29, 56]:  # 왼쪽 Shift, Ctrl, Alt
            return "왼쪽"
        elif scan_code in [54, 285, 312]:  # 오른쪽 Shift, Ctrl, Alt
            return "오른쪽"
        elif 71 <= scan_code <= 83:  # 숫자패드 영역
            return "숫자패드"
        return "메인"
        
    def _get_modifier_text(self):
        """수정자 키 텍스트 생성"""
        modifiers = self.last_key_info['modifiers']
        mod_texts = []
        
        if modifiers & Qt.ShiftModifier:
            mod_texts.append("Shift")
        if modifiers & Qt.ControlModifier:
            mod_texts.append("Ctrl")
        if modifiers & Qt.AltModifier:
            mod_texts.append("Alt")
            
        return " + ".join(mod_texts) if mod_texts else "없음"
        
    def accept(self):
        """저장 버튼 클릭 시 처리"""
        if self.last_key_info:
            self.key_selected.emit(self.last_key_info)
        super().accept()
