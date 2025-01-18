from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QGuiApplication
from ....utils.key_handler import format_key_info
from ..common.key_input_widget import KeyInputWidget

class KeyInputDialog(QDialog):
    """키 입력을 받는 다이얼로그"""
    
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
        KeyInputLayout__QVBoxLayout = QVBoxLayout()
        
        # 안내 메시지
        GuideLabel__QLabel = QLabel("입력하려는 키를 누르세요")
        GuideLabel__QLabel.setAlignment(Qt.AlignCenter)
        KeyInputLayout__QVBoxLayout.addWidget(GuideLabel__QLabel)
        
        # NumLock 경고 메시지
        self.NumLockWarning__QLabel = QLabel()
        self.NumLockWarning__QLabel.setStyleSheet("color: red;")
        self.NumLockWarning__QLabel.setAlignment(Qt.AlignCenter)
        self.NumLockWarning__QLabel.setWordWrap(True)
        KeyInputLayout__QVBoxLayout.addWidget(self.NumLockWarning__QLabel)
        
        # 키 입력 위젯
        self.KeyInputWidget__KeyInputWidget = KeyInputWidget(self, show_details=True)
        KeyInputLayout__QVBoxLayout.addWidget(self.KeyInputWidget__KeyInputWidget)
        
        # 키 정보 라벨
        self.KeyInfoLabel__QLabel = QLabel()
        self.KeyInfoLabel__QLabel.setWordWrap(True)
        KeyInputLayout__QVBoxLayout.addWidget(self.KeyInfoLabel__QLabel)
        
        # 버튼 레이아웃
        KeyInputButtonSection__QHBoxLayout = QHBoxLayout()
        
        # 확인 버튼
        self.ConfirmButton__QPushButton = QPushButton("입력된 키 정보 저장")
        self.ConfirmButton__QPushButton.clicked.connect(self._on_confirm)
        KeyInputButtonSection__QHBoxLayout.addWidget(self.ConfirmButton__QPushButton)
        
        # 취소 버튼
        self.CancelButton__QPushButton = QPushButton("키 입력 취소")
        self.CancelButton__QPushButton.clicked.connect(self.reject)
        KeyInputButtonSection__QHBoxLayout.addWidget(self.CancelButton__QPushButton)
        
        KeyInputLayout__QVBoxLayout.addLayout(KeyInputButtonSection__QHBoxLayout)
        self.setLayout(KeyInputLayout__QVBoxLayout)

    def keyPressEvent(self, event: QKeyEvent):
        """키 이벤트 처리"""
        # ESC와 Enter 키를 무시
        if event.key() in [Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter]:
            event.ignore()
        else:
            super().keyPressEvent(event)
        
    def _on_confirm(self):
        """확인 버튼 클릭 시"""
        key_info = self.KeyInputWidget__KeyInputWidget.get_key_info()
        if key_info:
            self.accept()
        
    def get_key_info(self):
        """현재 입력된 키 정보 반환"""
        return self.KeyInputWidget__KeyInputWidget.get_key_info()