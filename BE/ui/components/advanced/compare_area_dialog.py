from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                              QLabel, QPushButton, QFrame, QLineEdit,
                              QGridLayout, QWidget)
from PySide6.QtCore import Qt
from ..process_selector.process_selector_dialog import ProcessSelectorDialog

class CompareAreaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("실시간 비교 영역 관리")
        self.setFixedSize(600, 500)
        
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
        
        # 캡처된 영역 정보
        self.captured_area_info = QLabel("캡처된 영역이 없습니다")
        self.captured_area_info.setWordWrap(True)
        layout.addWidget(self.captured_area_info)
        
        # 캡처 영역 좌표 입력 필드들을 포함할 수평 레이아웃
        coordinates_container = QHBoxLayout()
        
        # 캡처 영역 좌표 입력 필드들
        coordinates_frame = QFrame()
        coordinates_frame.setFrameStyle(QFrame.Panel | QFrame.Raised)
        coordinates_layout = QGridLayout()
        coordinates_layout.setSpacing(10)
        coordinates_layout.setContentsMargins(10, 10, 10, 10)
        
        # 좌상단 좌표
        top_left_layout = QHBoxLayout()
        top_left_layout.addWidget(QLabel("좌상단:"))
        self.top_left_x = QLineEdit()
        self.top_left_x.setReadOnly(True)
        self.top_left_x.setPlaceholderText("X")
        self.top_left_x.setFixedWidth(60)
        top_left_layout.addWidget(self.top_left_x)
        self.top_left_y = QLineEdit()
        self.top_left_y.setReadOnly(True)
        self.top_left_y.setPlaceholderText("Y")
        self.top_left_y.setFixedWidth(60)
        top_left_layout.addWidget(self.top_left_y)
        top_left_widget = QWidget()
        top_left_widget.setLayout(top_left_layout)
        coordinates_layout.addWidget(top_left_widget, 0, 0)
        
        # 우상단 좌표
        top_right_layout = QHBoxLayout()
        top_right_layout.addWidget(QLabel("우상단:"))
        self.top_right_x = QLineEdit()
        self.top_right_x.setReadOnly(True)
        self.top_right_x.setPlaceholderText("X")
        self.top_right_x.setFixedWidth(60)
        top_right_layout.addWidget(self.top_right_x)
        self.top_right_y = QLineEdit()
        self.top_right_y.setReadOnly(True)
        self.top_right_y.setPlaceholderText("Y")
        self.top_right_y.setFixedWidth(60)
        top_right_layout.addWidget(self.top_right_y)
        top_right_widget = QWidget()
        top_right_widget.setLayout(top_right_layout)
        coordinates_layout.addWidget(top_right_widget, 0, 1)
        
        # 좌하단 좌표
        bottom_left_layout = QHBoxLayout()
        bottom_left_layout.addWidget(QLabel("좌하단:"))
        self.bottom_left_x = QLineEdit()
        self.bottom_left_x.setReadOnly(True)
        self.bottom_left_x.setPlaceholderText("X")
        self.bottom_left_x.setFixedWidth(60)
        bottom_left_layout.addWidget(self.bottom_left_x)
        self.bottom_left_y = QLineEdit()
        self.bottom_left_y.setReadOnly(True)
        self.bottom_left_y.setPlaceholderText("Y")
        self.bottom_left_y.setFixedWidth(60)
        bottom_left_layout.addWidget(self.bottom_left_y)
        bottom_left_widget = QWidget()
        bottom_left_widget.setLayout(bottom_left_layout)
        coordinates_layout.addWidget(bottom_left_widget, 1, 0)
        
        # 우하단 좌표
        bottom_right_layout = QHBoxLayout()
        bottom_right_layout.addWidget(QLabel("우하단:"))
        self.bottom_right_x = QLineEdit()
        self.bottom_right_x.setReadOnly(True)
        self.bottom_right_x.setPlaceholderText("X")
        self.bottom_right_x.setFixedWidth(60)
        bottom_right_layout.addWidget(self.bottom_right_x)
        self.bottom_right_y = QLineEdit()
        self.bottom_right_y.setReadOnly(True)
        self.bottom_right_y.setPlaceholderText("Y")
        self.bottom_right_y.setFixedWidth(60)
        bottom_right_layout.addWidget(self.bottom_right_y)
        bottom_right_widget = QWidget()
        bottom_right_widget.setLayout(bottom_right_layout)
        coordinates_layout.addWidget(bottom_right_widget, 1, 1)
        
        coordinates_frame.setLayout(coordinates_layout)
        coordinates_container.addWidget(coordinates_frame)
        coordinates_container.addStretch()
        layout.addLayout(coordinates_container)
        
        # 캡처 이미지 표시 영역
        capture_frame = QFrame()
        capture_frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
        """)
        capture_frame.setMinimumHeight(150)
        
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
        self.cancel_btn.clicked.connect(self.reject)  # 취소 버튼에 reject 연결
        
    def _select_process(self):
        """프로세스 선택"""
        dialog = ProcessSelectorDialog(self)
        if dialog.exec_():
            selected_process = dialog.selected_process
            if selected_process:
                process_info_text = f"선택된 프로세스 [PID: {selected_process['pid']}] {selected_process['name']} - {selected_process['title']}"
                self.process_info.setText(process_info_text)
                self.capture_btn.setEnabled(True)
        
    def _reset_process(self):
        """프로세스 초기화"""
        self.process_info.setText("선택된 프로세스 없음")
        self.capture_btn.setEnabled(False)