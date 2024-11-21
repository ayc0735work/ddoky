from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QLineEdit, QFrame, QListWidget,
                           QListWidgetItem, QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("또키 - 종합 매크로")
        self.setFixedSize(1200, 1000)
        
        # 폰트 설정
        title_font = QFont("Noto Sans CJK KR", 20, QFont.Weight.Bold)
        section_font = QFont("Noto Sans CJK KR", 14, QFont.Weight.Bold)
        
        # 메인 위젯과 레이아웃
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 타이틀
        title = QLabel("또키 - 종합 매크로")
        title.setFont(title_font)
        main_layout.addWidget(title)
        
        # 상단 컨텐츠 영역
        content_layout = QHBoxLayout()
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 만든 직 영역
        logic_list = QFrame()
        logic_layout = QVBoxLayout()
        logic_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        logic_title = QLabel("만든 로직 영역")
        logic_title.setFont(section_font)
        logic_layout.addWidget(logic_title)
        
        # 만든 로직 목록
        self.logic_listwidget = QListWidget()
        self.logic_listwidget.setFixedSize(325, 400)
        for i in range(1, 7):
            item_text = f"키보드 A 입력" if i > 3 else f"{'ABCD'[i-1]*4} 로직"
            item = QListWidgetItem(f"{i}. {item_text}")
            self.logic_listwidget.addItem(item)
            
        logic_layout.addWidget(self.logic_listwidget)
        
        # 10px 간격 추가
        spacer = QWidget()
        spacer.setFixedHeight(10)
        logic_layout.addWidget(spacer)
        
        # 만든 로직 버튼 영역
        logic_buttons_layout = QHBoxLayout()
        self.up_btn = QPushButton("↑")
        self.down_btn = QPushButton("↓")
        self.edit_btn = QPushButton("수정")
        self.delete_btn = QPushButton("삭제")
        
        # 버튼들의 크기를 동일하게 설정
        for btn in [self.up_btn, self.down_btn, self.edit_btn, self.delete_btn]:
            btn.setFixedWidth(280//4)  # 목록 상자 너비를 4등분
            logic_buttons_layout.addWidget(btn)
            
        # 버튼 클릭 이벤트 연결
        self.up_btn.clicked.connect(self.on_up_clicked)
        self.down_btn.clicked.connect(self.on_down_clicked)
        self.edit_btn.clicked.connect(self.on_edit_clicked)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        
        logic_layout.addLayout(logic_buttons_layout)
        logic_list.setLayout(logic_layout)
        logic_list.setFixedSize(345, 480)
        
        # 로직 순서 영역
        order_frame = QFrame()
        order_layout = QVBoxLayout()
        order_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 로직 순서 타이틀
        order_title = QLabel("로직 순서 영역")
        order_title.setFont(section_font)
        order_layout.addWidget(order_title)
        
        # 로직 이름 입력 영역
        name_layout = QHBoxLayout()
        name_label = QLabel("로직 이름")
        name_layout.addWidget(name_label)
        name_layout.addWidget(QLineEdit())
        save_btn = QPushButton("저장")
        reset_btn = QPushButton("초기화")
        name_layout.addWidget(save_btn)
        name_layout.addWidget(reset_btn)
        
        order_layout.addLayout(name_layout)
        
        # 로직 순서 목록
        self.order_listwidget = QListWidget()
        self.order_listwidget.setFixedSize(325, 370)
        for i in range(1, 7):
            item = QListWidgetItem(f"{i}. 키보드 A 입력")
            self.order_listwidget.addItem(item)
            
        order_layout.addWidget(self.order_listwidget)
        
        # 10px 간격 추가
        spacer2 = QWidget()
        spacer2.setFixedHeight(10)
        order_layout.addWidget(spacer2)
        
        # 로직 순서 버튼 영역
        order_buttons_layout = QHBoxLayout()
        self.order_up_btn = QPushButton("↑")
        self.order_down_btn = QPushButton("↓")
        self.order_edit_btn = QPushButton("수정")
        self.order_delete_btn = QPushButton("삭제")
        
        # 버튼들의 크기를 동일하게 설정
        for btn in [self.order_up_btn, self.order_down_btn, self.order_edit_btn, self.order_delete_btn]:
            btn.setFixedWidth(280//4)  # 목록 상자 너비를 4등분
            order_buttons_layout.addWidget(btn)
            
        # 버튼 클릭 이벤트 연결
        self.order_up_btn.clicked.connect(self.on_order_up_clicked)
        self.order_down_btn.clicked.connect(self.on_order_down_clicked)
        self.order_edit_btn.clicked.connect(self.on_order_edit_clicked)
        self.order_delete_btn.clicked.connect(self.on_order_delete_clicked)
        
        order_layout.addLayout(order_buttons_layout)
        order_frame.setLayout(order_layout)
        order_frame.setFixedSize(345, 480)
        
        # 로직 구성 도구 영역
        tools_frame = QFrame()
        tools_layout = QVBoxLayout()
        tools_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 로직 구성 도구 이틀
        tools_title = QLabel("로직 구성 도구")
        tools_title.setFont(section_font)
        tools_layout.addWidget(tools_title)
        
        # 도구 버튼 생성 및 이벤트 연결
        self.record_btn = QPushButton("기록 모드")
        self.key_input_btn = QPushButton("키 입력 추가")
        self.mouse_input_btn = QPushButton("마우스 입력 추가")
        self.delay_btn = QPushButton("지연시간 추가")
        
        # 버튼을 레이아웃에 추가
        tools_layout.addWidget(self.record_btn)
        tools_layout.addWidget(self.key_input_btn)
        tools_layout.addWidget(self.mouse_input_btn)
        tools_layout.addWidget(self.delay_btn)
        
        # 버튼 클릭 이벤트 연결
        self.record_btn.clicked.connect(self.on_record_clicked)
        self.key_input_btn.clicked.connect(self.on_key_input_clicked)
        self.mouse_input_btn.clicked.connect(self.on_mouse_input_clicked)
        self.delay_btn.clicked.connect(self.on_delay_clicked)
        
        tools_frame.setLayout(tools_layout)
        tools_frame.setFixedSize(200, 480)
        
        # 컨텐츠 레이아웃에 위젯 추가
        content_layout.addWidget(logic_list)
        content_layout.addWidget(order_frame)
        content_layout.addWidget(tools_frame)
        
        main_layout.addLayout(content_layout)
        
        # 40px 간격 추가
        top_spacer = QWidget()
        top_spacer.setFixedHeight(40)
        main_layout.addWidget(top_spacer)
        
        # 고급 기능 영역
        advanced_frame = QFrame()
        advanced_layout = QVBoxLayout()
        advanced_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        advanced_title = QLabel("고급 기능 영역")
        advanced_title.setFont(section_font)
        advanced_layout.addWidget(advanced_title)
        
        # 내용을 담을 내부 프레임 추가
        inner_frame = QFrame()
        inner_frame.setStyleSheet("""
            QFrame {
                border: 1px solid black;
                background-color: white;
            }
        """)
        inner_frame.setFixedSize(890, 160)  # 타이틀 영역을 제외한 크기
        advanced_layout.addWidget(inner_frame)
        
        advanced_frame.setLayout(advanced_layout)
        advanced_frame.setFixedSize(890, 200)
        main_layout.addWidget(advanced_frame)
        
        # 40px 간격 추가
        middle_spacer = QWidget()
        middle_spacer.setFixedHeight(40)
        main_layout.addWidget(middle_spacer)
        
        # 로그 영역
        log_frame = QFrame()
        log_layout = QVBoxLayout()
        log_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        log_title = QLabel("로그 영역")
        log_title.setFont(section_font)
        log_layout.addWidget(log_title)
        
        log_text = QTextEdit()
        log_text.setReadOnly(True)
        log_layout.addWidget(log_text)
        
        log_frame.setLayout(log_layout)
        log_frame.setFixedSize(890, 200)  # 세 영역의 너비 합계
        main_layout.addWidget(log_frame)
        
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # 스타일 설정
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
        self.order_listwidget.setStyleSheet(list_style)
        
        # 버튼 스타일 적용
        for btn in [self.up_btn, self.down_btn, self.edit_btn, self.delete_btn,
                   self.order_up_btn, self.order_down_btn, self.order_edit_btn, self.order_delete_btn,
                   self.record_btn, self.key_input_btn, self.mouse_input_btn, self.delay_btn]:
            btn.setStyleSheet(button_style)
            
    def on_up_clicked(self):
        print("위로 이동 버튼 클릭됨")
        current_row = self.logic_listwidget.currentRow()
        if current_row > 0:
            item = self.logic_listwidget.takeItem(current_row)
            self.logic_listwidget.insertItem(current_row - 1, item)
            self.logic_listwidget.setCurrentRow(current_row - 1)
            
    def on_down_clicked(self):
        print("아래로 이동 버튼 클릭됨")
        current_row = self.logic_listwidget.currentRow()
        if current_row < self.logic_listwidget.count() - 1:
            item = self.logic_listwidget.takeItem(current_row)
            self.logic_listwidget.insertItem(current_row + 1, item)
            self.logic_listwidget.setCurrentRow(current_row + 1)
            
    def on_edit_clicked(self):
        print("수정 버튼 클릭됨")
        current_item = self.logic_listwidget.currentItem()
        if current_item:
            print(f"Edit item: {current_item.text()}")
            
    def on_delete_clicked(self):
        print("삭제 버튼 클릭됨")
        current_row = self.logic_listwidget.currentRow()
        if current_row >= 0:
            self.logic_listwidget.takeItem(current_row)
            
    def on_order_up_clicked(self):
        print("순서 위로 이동 버튼 클릭됨")
        current_row = self.order_listwidget.currentRow()
        if current_row > 0:
            item = self.order_listwidget.takeItem(current_row)
            self.order_listwidget.insertItem(current_row - 1, item)
            self.order_listwidget.setCurrentRow(current_row - 1)
            
    def on_order_down_clicked(self):
        print("순서 아래로 이동 버튼 클릭됨")
        current_row = self.order_listwidget.currentRow()
        if current_row < self.order_listwidget.count() - 1:
            item = self.order_listwidget.takeItem(current_row)
            self.order_listwidget.insertItem(current_row + 1, item)
            self.order_listwidget.setCurrentRow(current_row + 1)
            
    def on_order_edit_clicked(self):
        print("순서 수정 버튼 클릭됨")
        current_item = self.order_listwidget.currentItem()
        if current_item:
            print(f"Edit order item: {current_item.text()}")
            
    def on_order_delete_clicked(self):
        print("순서 삭제 버튼 클릭됨")
        current_row = self.order_listwidget.currentRow()
        if current_row >= 0:
            self.order_listwidget.takeItem(current_row)
            
    def on_record_clicked(self):
        print("기록 모드 클릭됨")
        
    def on_key_input_clicked(self):
        print("키 입력 추가 클릭됨")
        
    def on_mouse_input_clicked(self):
        print("마우스 입력 추가 클릭됨")
        
    def on_delay_clicked(self):
        print("지연시간 추가 클릭됨")