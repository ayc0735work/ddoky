from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Signal
from PySide6.QtGui import QFont
from ..constants.styles import TITLE_FONT_FAMILY, SECTION_FONT_SIZE

class EtcFunctionWidget(QWidget):
    """기타 기능 위젯"""
    
    # 시그널 정의
    log_message = Signal(str)  # 로그 메시지 시그널
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        # 메인 레이아웃
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # 제목 레이블
        title_label = QLabel("기타 기능 영역")
        title_font = QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
        title_font.setWeight(QFont.Bold)
        title_label.setFont(title_font)
        self.main_layout.addWidget(title_label)
        
        # 버튼 레이아웃
        self.button_layout = QHBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        
        # 기타 기능 버튼들 추가
        self.add_function_buttons()
        
    def add_function_buttons(self):
        """기타 기능 버튼들 추가"""
        # 여기에 필요한 기타 기능 버튼들을 추가
        # 예시:
        self.add_button("기능 1", self.function1)
        self.add_button("기능 2", self.function2)
        
    def add_button(self, text, callback):
        """버튼 추가 헬퍼 메서드"""
        button = QPushButton(text)
        button.clicked.connect(callback)
        self.button_layout.addWidget(button)
        
    def function1(self):
        """기능 1"""
        self.log_message.emit("기능 1이 실행되었습니다.")
        
    def function2(self):
        """기능 2"""
        self.log_message.emit("기능 2가 실행되었습니다.")
