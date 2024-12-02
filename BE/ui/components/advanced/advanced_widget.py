from PySide6.QtWidgets import (QFrame, QVBoxLayout, QLabel, 
                               QHBoxLayout, QCheckBox, QSlider, QSpinBox, QPushButton, QProgressBar, QWidget)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...constants.styles import (FRAME_STYLE, CONTAINER_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import ADVANCED_FRAME_WIDTH, ADVANCED_SECTION_HEIGHT
from BE.ui.components.logic_maker.logic_selector_dialog import LogicSelectorDialog

class CustomSpinBox(QSpinBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSuffix(" / 100")
        self.setRange(0, 100)
        self.setValue(50)  # 기본값
        self.setFixedWidth(80)
        
        # 라인에딧의 선택 가능 범위를 제한
        self.lineEdit().selectionChanged.connect(self._limit_selection)
    
    def _limit_selection(self):
        # 현재 선택된 텍스트 범위
        start = self.lineEdit().selectionStart()
        end = self.lineEdit().selectionEnd()
        
        # 숫자 부분의 길이
        num_length = len(str(self.value()))
        
        # 선택 범위가 숫자 부분을 벗어나면 선택을 제한
        if end > num_length:
            self.lineEdit().setSelection(start, num_length)
    
    def focusInEvent(self, event):
        super().focusInEvent(event)
        # 텍스트 선택을 지우고 커서를 숫자 끝으로 이동
        self.lineEdit().deselect()
        self.lineEdit().setCursorPosition(len(str(self.value())))
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        # suffix 부분을 클릭한 경우 커서를 숫자 끝으로 이동
        cursor_pos = self.lineEdit().cursorPosition()
        if cursor_pos > len(str(self.value())):
            self.lineEdit().setCursorPosition(len(str(self.value())))

class AdvancedWidget(QWidget):
    """고급 기능을 위한 위젯"""
    
    # 시그널 정의
    advanced_action = Signal(str)  # 고급 기능 액션이 발생했을 때
    log_message = Signal(str)  # 로그 메시지 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self._connect_signals()
        
        # 선택된 로직 정보 저장
        self.hp_selected_logic = None
        self.mp_selected_logic = None
        self.saved_logics = {}  # 저장된 로직 정보
    
    def _connect_signals(self):
        """시그널 연결"""
        # 체력 로직 관련 시그널
        self.hp_logic_select_btn.clicked.connect(lambda: self._show_logic_select_dialog('hp'))
        self.hp_logic_reset_btn.clicked.connect(lambda: self._reset_logic('hp'))
        
        # 마력 로직 관련 시그널
        self.mp_logic_select_btn.clicked.connect(lambda: self._show_logic_select_dialog('mp'))
        self.mp_logic_reset_btn.clicked.connect(lambda: self._reset_logic('mp'))
        
        # 게이지 값 변경 시그널
        self.hp_slider.valueChanged.connect(self.hp_spinbox.setValue)
        self.hp_spinbox.valueChanged.connect(self.hp_slider.setValue)
        self.mp_slider.valueChanged.connect(self.mp_spinbox.setValue)
        self.mp_spinbox.valueChanged.connect(self.mp_slider.setValue)
    
    def _show_logic_select_dialog(self, type_):
        """로직 선택 다이얼로그 표시"""
        dialog = LogicSelectorDialog(self.saved_logics, self)
        if dialog.exec_():
            selected_logic = dialog.selected_logic
            if selected_logic and selected_logic in self.saved_logics:
                logic_info = self.saved_logics[selected_logic]
                logic_name = logic_info.get('name', '알 수 없는 로직')
                if type_ == 'hp':
                    self.hp_selected_logic = selected_logic
                    self.hp_logic_name.setText(logic_name)
                    self.hp_logic_name.setWordWrap(True)
                    self.hp_logic_checkbox.setEnabled(True)
                    self.hp_logic_checkbox.setChecked(True)
                else:
                    self.mp_selected_logic = selected_logic
                    self.mp_logic_name.setText(logic_name)
                    self.mp_logic_name.setWordWrap(True)
                    self.mp_logic_checkbox.setEnabled(True)
                    self.mp_logic_checkbox.setChecked(True)
    
    def _reset_logic(self, type_):
        """로직 초기화"""
        if type_ == 'hp':
            self.hp_selected_logic = None
            self.hp_logic_name.setText("선택된 로직 없음")
            self.hp_logic_checkbox.setChecked(False)
            self.hp_logic_checkbox.setEnabled(False)
        else:
            self.mp_selected_logic = None
            self.mp_logic_name.setText("선택된 로직 없음")
            self.mp_logic_checkbox.setChecked(False)
            self.mp_logic_checkbox.setEnabled(False)
    
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedWidth(ADVANCED_FRAME_WIDTH)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        
        # 타이틀
        title = QLabel("고급 기능 영역")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 고급 기능 컨테이너
        container = QFrame()
        container.setStyleSheet(CONTAINER_STYLE)
        container.setFixedSize(ADVANCED_FRAME_WIDTH - 20, ADVANCED_SECTION_HEIGHT)
        
        # 컨테이너 레이아웃
        container_layout = QVBoxLayout()
        container_layout.setSpacing(20)
        container_layout.setContentsMargins(10, 5, 10, 5)
        container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 회복 기준 섹션 프레임
        recovery_frame = QFrame()
        recovery_frame.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border: none;
            }
        """)
        recovery_layout = QVBoxLayout()
        recovery_layout.setSpacing(15)  # 섹션 간 간격
        recovery_layout.setContentsMargins(0, 0, 0, 0)
        
        # 체력 섹션
        hp_section = QVBoxLayout()
        hp_section.setSpacing(10)
        
        # 체력 게이지와 로직 영역을 담을 수평 레이아웃
        hp_content_layout = QHBoxLayout()
        hp_content_layout.setSpacing(20)
        
        # 체력 게이지 영역
        hp_gauge_frame = QFrame()
        hp_gauge_frame.setStyleSheet("QFrame { background-color: transparent; }")
        hp_gauge_layout = QHBoxLayout()
        hp_gauge_layout.setContentsMargins(0, 0, 0, 0)
        hp_gauge_layout.setSpacing(20)
        
        hp_label = QLabel("체력 회복 기준")
        hp_label.setFixedWidth(80)
        hp_gauge_layout.addWidget(hp_label)
        
        self.hp_slider = QSlider(Qt.Horizontal)
        self.hp_slider.setRange(0, 100)
        self.hp_slider.setValue(50)
        self.hp_slider.setFixedWidth(200)
        self.hp_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #f0f0f0;
                height: 10px;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #ff6b6b;
                width: 16px;
                margin: -3px 0;
                border-radius: 8px;
            }
        """)
        hp_gauge_layout.addWidget(self.hp_slider)
        
        self.hp_spinbox = CustomSpinBox()
        hp_gauge_layout.addWidget(self.hp_spinbox)
        hp_gauge_layout.addStretch()
        
        hp_gauge_frame.setLayout(hp_gauge_layout)
        hp_content_layout.addWidget(hp_gauge_frame)
        
        # 체력 로직 동작 영역
        hp_logic_frame = QFrame()
        hp_logic_frame.setStyleSheet("QFrame { background-color: transparent; }")
        hp_logic_layout = QVBoxLayout()
        hp_logic_layout.setContentsMargins(0, 0, 0, 0)
        hp_logic_layout.setSpacing(5)
        
        # 체크박스와 로직 이름 레이아웃
        hp_logic_header = QHBoxLayout()
        hp_logic_header.setContentsMargins(0, 0, 0, 0)
        self.hp_logic_checkbox = QCheckBox("동작할 로직")
        self.hp_logic_checkbox.setEnabled(False)
        hp_logic_header.addWidget(self.hp_logic_checkbox)
        
        self.hp_logic_name = QLabel("선택된 로직 없음")
        self.hp_logic_name.setWordWrap(True)
        hp_logic_header.addWidget(self.hp_logic_name, 1)
        
        hp_logic_layout.addLayout(hp_logic_header)
        
        # 버튼 레이아웃
        hp_button_layout = QHBoxLayout()
        hp_button_layout.setSpacing(10)
        
        # 로직 선택 버튼
        self.hp_logic_select_btn = QPushButton("로직 선택")
        self.hp_logic_select_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        hp_button_layout.addWidget(self.hp_logic_select_btn, 1)
        
        # 로직 초기화 버튼
        self.hp_logic_reset_btn = QPushButton("로직 초기화")
        self.hp_logic_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        hp_button_layout.addWidget(self.hp_logic_reset_btn, 1)
        
        hp_logic_layout.addLayout(hp_button_layout)
        hp_logic_frame.setLayout(hp_logic_layout)
        hp_content_layout.addWidget(hp_logic_frame, 1)  # stretch factor 1
        
        hp_section.addLayout(hp_content_layout)
        
        # 마력 섹션 (체력 섹션과 동일한 구조)
        mp_section = QVBoxLayout()
        mp_section.setSpacing(10)
        
        # 마력 게이지와 로직 영역을 담을 수평 레이아웃
        mp_content_layout = QHBoxLayout()
        mp_content_layout.setSpacing(20)
        
        # 마력 게이지 영역
        mp_gauge_frame = QFrame()
        mp_gauge_frame.setStyleSheet("QFrame { background-color: transparent; }")
        mp_gauge_layout = QHBoxLayout()
        mp_gauge_layout.setContentsMargins(0, 0, 0, 0)
        mp_gauge_layout.setSpacing(20)
        
        mp_label = QLabel("마력 회복 기준")
        mp_label.setFixedWidth(80)
        mp_gauge_layout.addWidget(mp_label)
        
        self.mp_slider = QSlider(Qt.Horizontal)
        self.mp_slider.setRange(0, 100)
        self.mp_slider.setValue(50)
        self.mp_slider.setFixedWidth(200)
        self.mp_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #f0f0f0;
                height: 10px;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #4dabf7;
                width: 16px;
                margin: -3px 0;
                border-radius: 8px;
            }
        """)
        mp_gauge_layout.addWidget(self.mp_slider)
        
        self.mp_spinbox = CustomSpinBox()
        mp_gauge_layout.addWidget(self.mp_spinbox)
        mp_gauge_layout.addStretch()
        
        mp_gauge_frame.setLayout(mp_gauge_layout)
        mp_content_layout.addWidget(mp_gauge_frame)
        
        # 마력 로직 동작 영역
        mp_logic_frame = QFrame()
        mp_logic_frame.setStyleSheet("QFrame { background-color: transparent; }")
        mp_logic_layout = QVBoxLayout()
        mp_logic_layout.setContentsMargins(0, 0, 0, 0)
        mp_logic_layout.setSpacing(5)
        
        # 체크박스와 로직 이름 레이아웃
        mp_logic_header = QHBoxLayout()
        mp_logic_header.setContentsMargins(0, 0, 0, 0)
        self.mp_logic_checkbox = QCheckBox("동작할 로직")
        self.mp_logic_checkbox.setEnabled(False)
        mp_logic_header.addWidget(self.mp_logic_checkbox)
        
        self.mp_logic_name = QLabel("선택된 로직 없음")
        self.mp_logic_name.setWordWrap(True)
        mp_logic_header.addWidget(self.mp_logic_name, 1)
        
        mp_logic_layout.addLayout(mp_logic_header)
        
        # 버튼 레이아웃
        mp_button_layout = QHBoxLayout()
        mp_button_layout.setSpacing(10)
        
        # 로직 선택 버튼
        self.mp_logic_select_btn = QPushButton("로직 선택")
        self.mp_logic_select_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        mp_button_layout.addWidget(self.mp_logic_select_btn, 1)
        
        # 로직 초기화 버튼
        self.mp_logic_reset_btn = QPushButton("로직 초기화")
        self.mp_logic_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        mp_button_layout.addWidget(self.mp_logic_reset_btn, 1)
        
        mp_logic_layout.addLayout(mp_button_layout)
        mp_logic_frame.setLayout(mp_logic_layout)
        mp_content_layout.addWidget(mp_logic_frame, 1)  # stretch factor 1
        
        mp_section.addLayout(mp_content_layout)
        
        # 섹션들을 메인 레이아웃에 추가
        recovery_layout.addLayout(hp_section)
        recovery_layout.addLayout(mp_section)
        
        recovery_frame.setLayout(recovery_layout)
        container_layout.addWidget(recovery_frame)
        
        # 공통 동작 로직 섹션
        common_frame = QFrame()
        common_frame.setStyleSheet("QFrame { background-color: transparent; border: none; }")
        common_layout = QVBoxLayout()
        common_layout.setContentsMargins(0, 15, 0, 0)  # 위쪽 여백 추가
        
        # 타이틀
        common_title = QLabel("공통 동작 로직")
        common_title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        common_layout.addWidget(common_title)
        
        # 공통 로직 컨텐츠 영역
        common_content_layout = QHBoxLayout()
        common_content_layout.setSpacing(20)
        
        # 공통 로직 정보 영역
        common_logic_frame = QFrame()
        common_logic_frame.setStyleSheet("QFrame { background-color: transparent; }")
        common_logic_layout = QVBoxLayout()
        common_logic_layout.setContentsMargins(0, 0, 0, 0)
        common_logic_layout.setSpacing(5)
        
        # 체크박스와 로직 이름 레이아웃
        common_logic_header = QHBoxLayout()
        common_logic_header.setContentsMargins(0, 0, 0, 0)
        self.common_logic_checkbox = QCheckBox("동작할 로직")
        self.common_logic_checkbox.setEnabled(False)
        common_logic_header.addWidget(self.common_logic_checkbox)
        
        self.common_logic_name = QLabel("선택된 로직 없음")
        self.common_logic_name.setWordWrap(True)
        common_logic_header.addWidget(self.common_logic_name, 1)
        
        common_logic_layout.addLayout(common_logic_header)
        
        # 버튼 레이아웃
        common_button_layout = QHBoxLayout()
        common_button_layout.setSpacing(10)
        
        # 로직 선택 버튼
        self.common_logic_select_btn = QPushButton("로직 선택")
        self.common_logic_select_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        common_button_layout.addWidget(self.common_logic_select_btn, 1)
        
        # 로직 초기화 버튼
        self.common_logic_reset_btn = QPushButton("로직 초기화")
        self.common_logic_reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: none;
                padding: 5px 10px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        common_button_layout.addWidget(self.common_logic_reset_btn, 1)
        
        common_logic_layout.addLayout(common_button_layout)
        common_logic_frame.setLayout(common_logic_layout)
        common_content_layout.addWidget(common_logic_frame, 1)  # stretch factor 1
        
        common_layout.addLayout(common_content_layout)
        common_frame.setLayout(common_layout)
        container_layout.addWidget(common_frame)
        
        container.setLayout(container_layout)
        layout.addWidget(container)
        
        self.setLayout(layout)
        
        # 시그널 연결
        self.hp_slider.valueChanged.connect(self.hp_spinbox.setValue)
        self.hp_spinbox.valueChanged.connect(self.hp_slider.setValue)
        self.mp_slider.valueChanged.connect(self.mp_spinbox.setValue)
        self.mp_spinbox.valueChanged.connect(self.mp_slider.setValue)
    
    def update_saved_logics(self, logics):
        """저장된 로직 정보 업데이트"""
        self.saved_logics = logics
