from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent, QGuiApplication
from ....utils.key_handler import format_key_info
from ..common.key_input_widget import KeyInputWidget

class KeyInputDialog(QDialog):
    """키 입력을 받는 다이얼로그"""
    
    key_selected = Signal(dict)  # 선택된 키 정보를 전달하는 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("키 입력")
        self.setFixedSize(400, 300)
        # ESC 키로 닫히는 것을 방지하기 위한 플래그 설정
        self.setWindowFlags(
            self.windowFlags() 
            & ~Qt.WindowContextHelpButtonHint 
            | Qt.WindowStaysOnTopHint 
            | Qt.CustomizeWindowHint 
            | Qt.WindowTitleHint 
            | Qt.WindowCloseButtonHint
        )
        
        self._setup_ui()
        
    def _setup_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        
        # 안내 메시지
        guide_label = QLabel("입력하려는 키를 누르세요")
        guide_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(guide_label)
        
        # NumLock 경고 메시지
        self.numlock_warning = QLabel()
        self.numlock_warning.setStyleSheet("color: red;")
        self.numlock_warning.setAlignment(Qt.AlignCenter)
        self.numlock_warning.setWordWrap(True)
        layout.addWidget(self.numlock_warning)
        
        # 키 입력 위젯
        self.key_input_widget = KeyInputWidget(self, show_details=True)
        self.key_input_widget.key_input_changed.connect(self._on_key_input_changed)
        layout.addWidget(self.key_input_widget)
        
        # 키 정보 라벨
        self.key_info_label = QLabel()
        self.key_info_label.setWordWrap(True)
        self.key_info_label.mousePressEvent = self._copy_key_info_to_clipboard # 
        self.key_info_label.setCursor(Qt.PointingHandCursor)  # 마우스 커서를 손가락 모양으로 변경
        layout.addWidget(self.key_info_label)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 확인 버튼
        confirm_button = QPushButton("키 입력 저장")
        confirm_button.clicked.connect(self._on_confirm)
        button_layout.addWidget(confirm_button)
        
        # 취소 버튼
        cancel_button = QPushButton("키 입력 취소")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def _on_key_input_changed(self, key_info):
        """키 입력이 변경되었을 때"""
        # NumLock 키 경고 처리
        if key_info.get('virtual_key') == 0x90:  # VK_NUMLOCK
            self.numlock_warning.setText("NumLock 키는 트리거 키로 사용할 수 없습니다.")
        else:
            self.numlock_warning.setText("")
        self.key_info_label.setText(format_key_info(key_info))
            
    def _on_confirm(self):
        """확인 버튼 클릭 시"""
        key_info = self.key_input_widget.get_key_info()
        if key_info:
            self.key_selected.emit(key_info)
            self.accept()
            
    def get_key_info(self):
        """현재 입력된 키 정보 반환"""
        return self.key_input_widget.get_key_info()
        
    def _copy_key_info_to_clipboard(self, event):
        """키 정보를 클립보드에 복사"""
        if self.key_info_label.text():
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.key_info_label.text())

    def keyPressEvent(self, event: QKeyEvent):
        """키 이벤트 처리"""
        # ESC와 Enter 키를 무시
        if event.key() in [Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter]:
            event.ignore()
        else:
            super().keyPressEvent(event)
