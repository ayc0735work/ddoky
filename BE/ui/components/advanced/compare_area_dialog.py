from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                              QLabel, QPushButton, QFrame)
from PySide6.QtCore import Qt

class CompareAreaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("실시간 비교 영역 관리")
        self.setFixedSize(600, 400)
        
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 프로세스 선택 영역
        process_frame = QFrame()
        process_frame.setStyleSheet("QFrame { background-color: transparent; }")
        process_layout = QVBoxLayout(process_frame)
        process_layout.setContentsMargins(0, 0, 0, 0)
        process_layout.setSpacing(5)
        
        # 프로세스 정보 표시 영역
        process_header = QHBoxLayout()
        self.process_info = QLabel("선택된 프로세스 없음")
        self.process_info.setWordWrap(True)
        process_header.addWidget(self.process_info)
        
        # 프로세스 선택 버튼 영역
        process_button_layout = QHBoxLayout()
        process_button_layout.setSpacing(10)
        
        self.process_select_btn = QPushButton("프로세스 선택")
        self.process_reset_btn = QPushButton("프로세스 초기화")
        
        button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        self.process_select_btn.setStyleSheet(button_style)
        self.process_reset_btn.setStyleSheet(button_style)
        
        process_button_layout.addWidget(self.process_select_btn)
        process_button_layout.addWidget(self.process_reset_btn)
        process_button_layout.addStretch()
        
        process_layout.addLayout(process_header)
        process_layout.addLayout(process_button_layout)
        
        layout.addWidget(process_frame)
        
        # 캡처 이미지 표시 영역
        capture_frame = QFrame()
        capture_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        capture_frame.setMinimumHeight(250)
        
        # 캡처 이미지가 없을 때 표시할 안내 텍스트
        guide_label = QLabel("캡처된 이미지가 없습니다.\n영역을 지정해주세요.")
        guide_label.setAlignment(Qt.AlignCenter)
        guide_label.setStyleSheet("color: #666;")
        
        capture_layout = QVBoxLayout(capture_frame)
        capture_layout.addWidget(guide_label)
        
        layout.addWidget(capture_frame)
        
        # 캡처 영역 관리 버튼들
        capture_button_layout = QHBoxLayout()
        capture_button_layout.setSpacing(10)
        
        self.capture_btn = QPushButton("캡처 영역 지정")
        self.capture_btn.setEnabled(False)  # 초기에는 비활성화
        self.reset_btn = QPushButton("캡처 영역 초기화")
        
        button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        self.capture_btn.setStyleSheet(button_style)
        self.reset_btn.setStyleSheet(button_style)
        
        capture_button_layout.addWidget(self.capture_btn)
        capture_button_layout.addWidget(self.reset_btn)
        capture_button_layout.addStretch()
        
        layout.addLayout(capture_button_layout)
        
        # 저장/취소 버튼
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.save_btn = QPushButton("저장")
        self.cancel_btn = QPushButton("취소")
        
        action_button_style = """
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3c8ce7;
            }
        """
        self.save_btn.setStyleSheet(action_button_style)
        
        cancel_button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """
        self.cancel_btn.setStyleSheet(cancel_button_style)
        
        button_layout.addStretch()
        button_layout.addWidget(self.save_btn)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 시그널 연결
        self.process_select_btn.clicked.connect(self._select_process)
        self.process_reset_btn.clicked.connect(self._reset_process)
        
    def _select_process(self):
        """프로세스 선택"""
        # TODO: 프로세스 선택 다이얼로그 표시
        # 임시로 프로세스가 선택되었다고 가정
        self.process_info.setText("선택된 프로세스 [PID: 1234] MapleStory - 메이플스토리")
        self.capture_btn.setEnabled(True)
        
    def _reset_process(self):
        """프로세스 초기화"""
        self.process_info.setText("선택된 프로세스 없음")
        self.capture_btn.setEnabled(False)
        