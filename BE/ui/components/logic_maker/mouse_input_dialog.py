from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                              QLabel, QComboBox, QSpinBox, QFrame, QRadioButton,
                              QButtonGroup)
from PySide6.QtCore import Qt, Signal
from win32api import GetCursorPos
from ..process_selector.process_selector_dialog import ProcessSelectorDialog

class MouseInputDialog(QDialog):
    """마우스 입력을 받는 다이얼로그"""
    
    mouse_input_selected = Signal(dict)  # 선택된 마우스 입력 정보를 전달하는 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("마우스 입력")
        self.setFixedSize(300, 600)
        self.setWindowFlags(
            self.windowFlags() 
            & ~Qt.WindowContextHelpButtonHint 
            | Qt.WindowStaysOnTopHint
        )
        
        self.selected_process = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # 프로세스 선택 섹션
        process_section = QFrame()
        process_section.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        process_layout = QVBoxLayout(process_section)
        
        process_title = QLabel("프로세스")
        process_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        process_layout.addWidget(process_title)
        
        # 프로세스 정보 표시
        self.process_info = QLabel("선택된 프로세스 없음")
        self.process_info.setWordWrap(True)
        process_layout.addWidget(self.process_info)
        
        # 프로세스 선택/초기화 버튼
        process_button_layout = QHBoxLayout()
        process_button_layout.setSpacing(10)
        
        self.process_select_btn = QPushButton("프로세스 선택")
        self.process_reset_btn = QPushButton("프로세스 초기화")
        
        button_style = """
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3d8ce4;
            }
        """
        self.process_select_btn.setStyleSheet(button_style)
        self.process_reset_btn.setStyleSheet(button_style)
        
        process_button_layout.addWidget(self.process_select_btn)
        process_button_layout.addWidget(self.process_reset_btn)
        process_layout.addLayout(process_button_layout)
        
        layout.addWidget(process_section)
        
        # 마우스 동작 선택 섹션
        action_section = QFrame()
        action_section.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        action_layout = QVBoxLayout(action_section)
        
        action_title = QLabel("마우스 동작")
        action_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        action_layout.addWidget(action_title)
        
        # 마우스 동작 라디오 버튼 그룹
        self.action_group = QButtonGroup()
        
        click_radio = QRadioButton("클릭")
        click_radio.setChecked(True)
        self.action_group.addButton(click_radio, 1)
        action_layout.addWidget(click_radio)
        
        move_radio = QRadioButton("이동")
        self.action_group.addButton(move_radio, 2)
        action_layout.addWidget(move_radio)
        
        drag_radio = QRadioButton("드래그")
        self.action_group.addButton(drag_radio, 3)
        action_layout.addWidget(drag_radio)
        
        layout.addWidget(action_section)
        
        # 마우스 버튼 선택 섹션
        button_section = QFrame()
        button_section.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        button_layout = QVBoxLayout(button_section)
        
        button_title = QLabel("마우스 버튼")
        button_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        button_layout.addWidget(button_title)
        
        self.button_combo = QComboBox()
        self.button_combo.addItems(["왼쪽 버튼", "오른쪽 버튼", "가운데 버튼"])
        self.button_combo.setStyleSheet("""
            QComboBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox::down-arrow {
                image: url(down_arrow.png);
                width: 12px;
                height: 12px;
            }
        """)
        button_layout.addWidget(self.button_combo)
        
        layout.addWidget(button_section)
        
        # 좌표 입력 섹션
        coord_section = QFrame()
        coord_section.setStyleSheet("QFrame { background-color: #f5f5f5; border-radius: 5px; padding: 10px; }")
        coord_layout = QVBoxLayout(coord_section)
        
        coord_title = QLabel("좌표")
        coord_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        coord_layout.addWidget(coord_title)
        
        # X 좌표
        x_layout = QHBoxLayout()
        x_label = QLabel("X:")
        self.x_spinbox = QSpinBox()
        self.x_spinbox.setRange(-9999, 9999)
        self.x_spinbox.setValue(0)
        self.x_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
            }
        """)
        x_layout.addWidget(x_label)
        x_layout.addWidget(self.x_spinbox)
        coord_layout.addLayout(x_layout)
        
        # Y 좌표
        y_layout = QHBoxLayout()
        y_label = QLabel("Y:")
        self.y_spinbox = QSpinBox()
        self.y_spinbox.setRange(-9999, 9999)
        self.y_spinbox.setValue(0)
        self.y_spinbox.setStyleSheet("""
            QSpinBox {
                padding: 5px;
                border: 1px solid #ccc;
                border-radius: 3px;
                background: white;
            }
        """)
        y_layout.addWidget(y_label)
        y_layout.addWidget(self.y_spinbox)
        coord_layout.addLayout(y_layout)
        
        # 현재 마우스 위치 가져오기 버튼
        get_pos_btn = QPushButton("현재 마우스 위치 가져오기")
        get_pos_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a9eff;
                color: white;
                border: none;
                padding: 8px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #3d8ce4;
            }
        """)
        coord_layout.addWidget(get_pos_btn)
        
        layout.addWidget(coord_section)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        confirm_btn = QPushButton("마우스 입력 정보 저장")
        confirm_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        cancel_btn = QPushButton("마우스 입력 취소")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 3px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        
        button_layout.addWidget(confirm_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        # 시그널 연결
        confirm_btn.clicked.connect(self._on_confirm)
        cancel_btn.clicked.connect(self.reject)
        get_pos_btn.clicked.connect(self._get_current_mouse_pos)
        self.process_select_btn.clicked.connect(self._select_process)
        self.process_reset_btn.clicked.connect(self._reset_process)
        
    def _get_current_mouse_pos(self):
        """현재 마우스 위치를 가져와서 spinbox에 설정"""
        try:
            x, y = GetCursorPos()
            self.x_spinbox.setValue(x)
            self.y_spinbox.setValue(y)
        except Exception as e:
            print(f"마우스 위치를 가져오는 중 오류 발생: {str(e)}")
            
    def _select_process(self):
        """프로세스 선택 다이얼로그 표시"""
        dialog = ProcessSelectorDialog(self)
        if dialog.exec():
            self.selected_process = dialog.selected_process
            if self.selected_process:
                process_info_text = f"[ PID : {self.selected_process['pid']} ] {self.selected_process['name']} - {self.selected_process['title']}"
                self.process_info.setText(process_info_text)
            
    def _reset_process(self):
        """프로세스 선택 초기화"""
        self.selected_process = None
        self.process_info.setText("선택된 프로세스 없음")
        
    def _on_confirm(self):
        """확인 버튼 클릭 시 호출"""
        # 선택된 정보 수집
        action_id = self.action_group.checkedId()
        action_map = {1: "클릭", 2: "이동", 3: "드래그"}
        action = action_map.get(action_id, "클릭")
        
        button = self.button_combo.currentText()
        x = self.x_spinbox.value()
        y = self.y_spinbox.value()
        
        # 마우스 입력 정보 생성
        mouse_info = {
            'type': 'mouse_input',
            'action': action,
            'button': button,
            'coordinates': {'x': x, 'y': y},
            'process': self.selected_process,
            'display_text': f"마우스 {action}: {button} ({x}, {y})"
        }
        
        # 시그널 발생
        self.mouse_input_selected.emit(mouse_info)
        self.accept() 