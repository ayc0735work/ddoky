from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QLineEdit, QFrame, QListWidget,
                           QListWidgetItem, QTextEdit, QSizePolicy)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sys

class LogRedirector:
    def __init__(self, text_widget):
        self.text_widget = text_widget
        self.original_stdout = sys.stdout

    def write(self, text):
        self.original_stdout.write(text)  # 터미널에도 출력
        if text.strip():  # 빈 줄이 아닌 경우에만 출력
            self.text_widget.append(text.rstrip())  # 오른쪽 공백과 줄바꿈 제거

    def flush(self):
        self.original_stdout.flush()

class MainWindow(QMainWindow):
    # 상수 정의
    WINDOW_WIDTH = 900
    WINDOW_HEIGHT = 1400
    TITLE_HEIGHT = 40
    BASIC_SECTION_HEIGHT = 480
    MIDDLE_SPACE = 20
    ADVANCED_SECTION_HEIGHT = 200
    LOG_SECTION_HEIGHT = 200
    
    FRAME_STYLE = "QFrame { background: transparent; border: none; }"
    CONTAINER_STYLE = """
        QFrame {
            background-color: #f8f8f8;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
    """
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("또키 - 종합 매크로")
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        
        # 폰트 설정
        self.title_font = QFont("Noto Sans CJK KR", 20, QFont.Weight.Bold)
        self.section_font = QFont("Noto Sans CJK KR", 14, QFont.Weight.Bold)
        
        # 레이아웃 초기화
        self.init_layouts()
        
        # UI 구성요소 초기화
        self.init_title()
        self.init_basic_features()
        self.init_advanced_features()
        
        # 메인 위젯 설정
        main_widget = QWidget()
        main_widget.setLayout(self.main_layout)
        self.setCentralWidget(main_widget)
        
        # 스타일 적용
        self.apply_styles()
    
    def init_layouts(self):
        """레이아웃 초기화"""
        # 메인 레이아웃
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(self.MIDDLE_SPACE)  # 레이아웃 간 간격 설정
        
        # 기본 기능 영역 레이아웃
        self.basic_features_layout = QHBoxLayout()
        self.basic_features_layout.setSpacing(0)
        
        # 고급 기능 영역 레이아웃
        self.advanced_features_layout = QHBoxLayout()
        self.advanced_features_layout.setSpacing(0)
        
        # 로그 영역 레이아웃
        self.log_layout = QHBoxLayout()
        self.log_layout.setSpacing(0)
    
    def init_title(self):
        """타이틀 초기화"""
        title = QLabel("또키 - 종합 매크로")
        title.setFont(self.title_font)
        self.main_layout.addWidget(title)
    
    def init_basic_features(self):
        """기본 기능 영역 초기화"""
        # 기본 기능 영역 레이아웃
        basic_features_layout = self.basic_features_layout
        
        # 로직 목록 영역
        logic_list = QFrame()
        logic_list.setStyleSheet(self.FRAME_STYLE)
        logic_layout = QVBoxLayout()
        logic_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        logic_layout.setContentsMargins(10, 10, 10, 10)
        
        logic_title = QLabel("만든 로직 영역")
        logic_title.setFont(self.section_font)
        logic_layout.addWidget(logic_title)
        
        self.logic_listwidget = QListWidget()
        self.logic_listwidget.setFixedSize(325, 380)
        for i in range(1, 7):
            item_text = f"키보드 A 입력" if i > 3 else f"{'ABCD'[i-1]*4} 로직"
            item = QListWidgetItem(f"{i}. {item_text}")
            self.logic_listwidget.addItem(item)
        logic_layout.addWidget(self.logic_listwidget)
        
        spacer = QWidget()
        spacer.setFixedHeight(30)
        logic_layout.addWidget(spacer)
        
        logic_buttons_layout = QHBoxLayout()
        self.up_btn = QPushButton("↑")
        self.down_btn = QPushButton("↓")
        self.edit_btn = QPushButton("수정")
        self.delete_btn = QPushButton("삭제")
        
        for btn in [self.up_btn, self.down_btn, self.edit_btn, self.delete_btn]:
            btn.setFixedWidth(280//4)
            logic_buttons_layout.addWidget(btn)
            btn.setEnabled(False)
        
        self.up_btn.clicked.connect(self.on_up_btn_clicked)
        self.down_btn.clicked.connect(self.on_down_btn_clicked)
        self.edit_btn.clicked.connect(self.on_edit_btn_clicked)
        self.delete_btn.clicked.connect(self.on_delete_btn_clicked)
        
        self.logic_listwidget.itemSelectionChanged.connect(self.on_logic_selection_changed)
        
        logic_layout.addLayout(logic_buttons_layout)
        logic_list.setLayout(logic_layout)
        logic_list.setFixedSize(345, self.BASIC_SECTION_HEIGHT)
        
        # 로직 구성 영역
        logic_detail_frame = QFrame()
        logic_detail_frame.setStyleSheet(self.FRAME_STYLE)
        logic_detail_layout = QVBoxLayout()
        logic_detail_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        logic_detail_layout.setContentsMargins(10, 10, 10, 10)
        
        logic_detail_title = QLabel("로직 구성 영역")
        logic_detail_title.setFont(self.section_font)
        logic_detail_layout.addWidget(logic_detail_title)
        
        self.logic_detail_listwidget = QListWidget()
        self.logic_detail_listwidget.setFixedSize(325, 350)
        for i in range(1, 7):
            item = QListWidgetItem(f"{i}. 키보드 A 입력")
            self.logic_detail_listwidget.addItem(item)
        logic_detail_layout.addWidget(self.logic_detail_listwidget)
        
        spacer2 = QWidget()
        spacer2.setFixedHeight(30)
        logic_detail_layout.addWidget(spacer2)
        
        logic_detail_buttons_layout = QHBoxLayout()
        self.logic_detail_up_btn = QPushButton("위로")
        self.logic_detail_down_btn = QPushButton("아래로")
        self.logic_detail_edit_btn = QPushButton("수정")
        self.logic_detail_delete_btn = QPushButton("삭제")
        
        for btn in [self.logic_detail_up_btn, self.logic_detail_down_btn, self.logic_detail_edit_btn, self.logic_detail_delete_btn]:
            btn.setFixedWidth(280//4)
            logic_detail_buttons_layout.addWidget(btn)
            btn.setEnabled(False)
        
        self.logic_detail_up_btn.clicked.connect(self.on_logic_detail_up_btn_clicked)
        self.logic_detail_down_btn.clicked.connect(self.on_logic_detail_down_btn_clicked)
        self.logic_detail_edit_btn.clicked.connect(self.on_logic_detail_edit_btn_clicked)
        self.logic_detail_delete_btn.clicked.connect(self.on_logic_detail_delete_btn_clicked)
        
        self.logic_detail_listwidget.itemSelectionChanged.connect(self.on_logic_detail_selection_changed)
        
        logic_detail_layout.addLayout(logic_detail_buttons_layout)
        logic_detail_frame.setLayout(logic_detail_layout)
        logic_detail_frame.setFixedSize(345, self.BASIC_SECTION_HEIGHT)
        
        # 로직 구성 메이커
        logic_detail_maker_frame = QFrame()
        logic_detail_maker_frame.setStyleSheet(self.FRAME_STYLE)
        logic_detail_maker_layout = QVBoxLayout()
        logic_detail_maker_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        logic_detail_maker_layout.setContentsMargins(10, 10, 10, 10)
        
        logic_detail_maker_title = QLabel("로직 구성 메이커")
        logic_detail_maker_title.setFont(self.section_font)
        logic_detail_maker_layout.addWidget(logic_detail_maker_title)
        
        self.key_input_btn = QPushButton("키 입력 추가")
        self.mouse_input_btn = QPushButton("마우스 입력 추가")
        self.delay_btn = QPushButton("지연시간 추가")
        self.record_btn = QPushButton("기록 모드")
        
        self.key_input_btn.clicked.connect(self.on_key_input_btn_clicked)
        self.mouse_input_btn.clicked.connect(self.on_mouse_input_btn_clicked)
        self.delay_btn.clicked.connect(self.on_delay_btn_clicked)
        self.record_btn.clicked.connect(self.on_record_btn_clicked)
        
        for btn in [self.key_input_btn, self.mouse_input_btn, self.delay_btn, self.record_btn]:
            btn.setFixedWidth(160)
            logic_detail_maker_layout.addWidget(btn)
        
        logic_detail_maker_frame.setLayout(logic_detail_maker_layout)
        logic_detail_maker_frame.setFixedSize(180, self.BASIC_SECTION_HEIGHT)
        
        basic_features_layout.addWidget(logic_list)
        basic_features_layout.addWidget(logic_detail_frame)
        basic_features_layout.addWidget(logic_detail_maker_frame)
        
        self.main_layout.addLayout(basic_features_layout)
    
    def init_advanced_features(self):
        """고급 기능 영역 초기화"""
        # 고급 기능 영역 레이아웃
        advanced_features_layout = self.advanced_features_layout
        
        advanced_frame = QFrame()
        advanced_frame.setStyleSheet(self.FRAME_STYLE)
        advanced_frame.setFixedWidth(870)
        advanced_layout = QVBoxLayout()
        advanced_layout.setContentsMargins(10, 10, 10, 10)
        
        advanced_title = QLabel("고급 기능 영역")
        advanced_title.setFont(self.section_font)
        advanced_layout.addWidget(advanced_title)
        
        advanced_container = QFrame()
        advanced_container.setStyleSheet(self.CONTAINER_STYLE)
        advanced_container.setFixedSize(850, self.ADVANCED_SECTION_HEIGHT)
        advanced_layout.addWidget(advanced_container)
        
        advanced_frame.setLayout(advanced_layout)
        advanced_features_layout.addWidget(advanced_frame)
        
        self.main_layout.addLayout(advanced_features_layout)
        
        # 로그 영역 초기화
        log_frame = QFrame()
        log_frame.setStyleSheet(self.FRAME_STYLE)
        log_frame.setFixedWidth(870)
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(10, 10, 10, 10)
        
        log_title = QLabel("로그 영역")
        log_title.setFont(self.section_font)
        log_layout.addWidget(log_title)
        
        log_container = QFrame()
        log_container.setStyleSheet(self.CONTAINER_STYLE)
        log_container.setMinimumSize(850, self.LOG_SECTION_HEIGHT)
        
        # 로그 컨테이너가 수직으로 늘어날 수 있도록 설정
        size_policy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        log_container.setSizePolicy(size_policy)
        
        # 로그 컨테이너 내부 레이아웃
        log_container_layout = QVBoxLayout()
        log_container.setLayout(log_container_layout)
        
        # 로그 출력을 위한 QTextEdit 추가
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)  # 읽기 전용으로 설정
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: none;
                font-family: 'Consolas', monospace;
                font-size: 12px;
                line-height: 0.5;
            }
        """)
        log_container_layout.addWidget(self.log_text)
        
        # 표준 출력을 로그로 리다이렉트
        sys.stdout = LogRedirector(self.log_text)
        
        log_layout.addWidget(log_container)
        
        log_frame.setLayout(log_layout)
        self.log_layout.addWidget(log_frame)
        
        self.main_layout.addLayout(self.log_layout)
    
    def apply_styles(self):
        """스타일 적용"""
        list_style = """
            QListWidget {
                border: 1px solid #ccc;
                background-color: white;
                border-radius: 4px;
            }
            QListWidget::item {
                height: 30px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #0078D7;
                color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #c1c1c1;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #a8a8a8;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """
        
        button_style = """
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 5px;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """
        
        self.logic_listwidget.setStyleSheet(list_style)
        self.logic_detail_listwidget.setStyleSheet(list_style)
        
        for btn in [self.up_btn, self.down_btn, self.edit_btn, self.delete_btn,
                   self.logic_detail_up_btn, self.logic_detail_down_btn, self.logic_detail_edit_btn, self.logic_detail_delete_btn,
                   self.record_btn, self.key_input_btn, self.mouse_input_btn, self.delay_btn]:
            btn.setStyleSheet(button_style)
    
    def on_up_btn_clicked(self):
        print("위로 이동 버튼 클릭됨")
        current_row = self.logic_listwidget.currentRow()
        if current_row > 0:
            item = self.logic_listwidget.takeItem(current_row)
            self.logic_listwidget.insertItem(current_row - 1, item)
            self.logic_listwidget.setCurrentRow(current_row - 1)
            
    def on_down_btn_clicked(self):
        print("아래로 이동 버튼 클릭됨")
        current_row = self.logic_listwidget.currentRow()
        if current_row < self.logic_listwidget.count() - 1:
            item = self.logic_listwidget.takeItem(current_row)
            self.logic_listwidget.insertItem(current_row + 1, item)
            self.logic_listwidget.setCurrentRow(current_row + 1)
            
    def on_edit_btn_clicked(self):
        print("수정 버튼 클릭됨")
        current_item = self.logic_listwidget.currentItem()
        if current_item:
            print(f"수정된 로직: {current_item.text()}")
            
    def on_delete_btn_clicked(self):
        print("삭제 버튼 클릭됨")
        current_row = self.logic_listwidget.currentRow()
        if current_row >= 0:
            item = self.logic_listwidget.takeItem(current_row)
            print(f"삭제된 로직: {item.text()}")
            
    def on_logic_detail_up_btn_clicked(self):
        print("순서 위로 이동 버튼 클릭됨")
        current_row = self.logic_detail_listwidget.currentRow()
        if current_row > 0:
            item = self.logic_detail_listwidget.takeItem(current_row)
            self.logic_detail_listwidget.insertItem(current_row - 1, item)
            self.logic_detail_listwidget.setCurrentRow(current_row - 1)
            
    def on_logic_detail_down_btn_clicked(self):
        print("순서 아래로 이동 버튼 클릭됨")
        current_row = self.logic_detail_listwidget.currentRow()
        if current_row < self.logic_detail_listwidget.count() - 1:
            item = self.logic_detail_listwidget.takeItem(current_row)
            self.logic_detail_listwidget.insertItem(current_row + 1, item)
            self.logic_detail_listwidget.setCurrentRow(current_row + 1)
            
    def on_logic_detail_edit_btn_clicked(self):
        print("순서 수정 버튼 클릭됨")
        current_item = self.logic_detail_listwidget.currentItem()
        if current_item:
            print(f"수정된 로직 구성: {current_item.text()}")
            
    def on_logic_detail_delete_btn_clicked(self):
        print("순서 삭제 버튼 클릭됨")
        current_row = self.logic_detail_listwidget.currentRow()
        if current_row >= 0:
            item = self.logic_detail_listwidget.takeItem(current_row)
            print(f"삭제된 로직 구성: {item.text()}")
            
    def on_record_btn_clicked(self):
        print("기록 모드 클릭됨")

    def on_key_input_btn_clicked(self):
        print("키 입력 추가 클릭됨")

    def on_mouse_input_btn_clicked(self):
        print("마우스 입력 추가 클릭됨")

    def on_delay_btn_clicked(self):
        print("지연시간 추가 클릭됨")

    def on_logic_selection_changed(self):
        if self.logic_listwidget.currentItem():
            self.up_btn.setEnabled(True)
            self.down_btn.setEnabled(True)
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(True)
        else:
            self.up_btn.setEnabled(False)
            self.down_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.delete_btn.setEnabled(False)

    def on_logic_detail_selection_changed(self):
        if self.logic_detail_listwidget.currentItem():
            self.logic_detail_up_btn.setEnabled(True)
            self.logic_detail_down_btn.setEnabled(True)
            self.logic_detail_edit_btn.setEnabled(True)
            self.logic_detail_delete_btn.setEnabled(True)
        else:
            self.logic_detail_up_btn.setEnabled(False)
            self.logic_detail_down_btn.setEnabled(False)
            self.logic_detail_edit_btn.setEnabled(False)
            self.logic_detail_delete_btn.setEnabled(False)
            
    def on_save_btn_clicked(self):
        print("저장 버튼 클릭됨")
        # TODO: 저장 로직 구현

    def on_reset_btn_clicked(self):
        print("초기화 버튼 클릭됨")
        # TODO: 초기화 로직 구현
