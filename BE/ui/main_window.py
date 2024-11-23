from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QLineEdit, QFrame, QListWidget,
                           QListWidgetItem, QTextEdit, QSizePolicy, QScrollArea)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
import sys

from .components.title.title_widget import TitleWidget
from .components.logic_list.logic_list_widget import LogicListWidget
from .components.logic_list.logic_list_controller import LogicListController
from .components.logic_detail.logic_detail_widget import LogicDetailWidget
from .components.logic_detail.logic_detail_controller import LogicDetailController
from .components.logic_maker.logic_maker_widget import LogicMakerWidget
from .components.logic_maker.logic_maker_controller import LogicMakerController
from .components.advanced.advanced_widget import AdvancedWidget
from .components.log.log_widget import LogWidget

from .constants.dimensions import (MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, BASIC_SECTION_HEIGHT,
                               MIDDLE_SPACE, ADVANCED_SECTION_HEIGHT)

class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self._setup_connections()  # 시그널/슬롯 연결 설정
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("또키 - 종합 매크로")
        self.setMinimumHeight(MAIN_WINDOW_HEIGHT)
        self.setFixedWidth(MAIN_WINDOW_WIDTH)
        
        # 스크롤 영역 생성
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 메인 위젯 생성
        main_widget = QWidget()
        
        # 레이아웃 초기화
        self.init_layouts()
        
        # UI 구성요소 초기화
        self.init_components()
        
        # 메인 위젯에 레이아웃 설정
        main_widget.setLayout(self.main_layout)
        
        # 스크롤 영역에 메인 위젯 설정
        scroll_area.setWidget(main_widget)
        
        # 중앙 위젯으로 스크롤 영역 설정
        self.setCentralWidget(scroll_area)
        
    def init_layouts(self):
        """레이아웃 초기화"""
        # 메인 레이아웃
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(MIDDLE_SPACE)
        
        # 기본 기능 영역 레이아웃
        self.basic_features_layout = QHBoxLayout()
        self.basic_features_layout.setSpacing(0)
        
        # 고급 기능 영역 레이아웃
        self.advanced_features_layout = QHBoxLayout()
        self.advanced_features_layout.setSpacing(0)
        
        # 로그 영역 레이아웃
        self.log_layout = QHBoxLayout()
        self.log_layout.setSpacing(0)
    
    def init_components(self):
        """UI 컴포넌트 초기화"""
        # 타이틀
        self.title_widget = TitleWidget()
        self.main_layout.addWidget(self.title_widget)
        
        # 기본 기능 영역
        self.init_basic_features()
        
        # 고급 기능 영역
        self.init_advanced_features()
        
        # 로그 영역
        self.init_log_features()
        
    def init_basic_features(self):
        """기본 기능 영역 초기화"""
        # 로직 리스트 위젯과 컨트롤러
        self.logic_list_widget = LogicListWidget()
        self.logic_list_controller = LogicListController(self.logic_list_widget)
        self.basic_features_layout.addWidget(self.logic_list_widget)
        
        # 로직 상세 정보 위젯과 컨트롤러
        self.logic_detail_widget = LogicDetailWidget()
        self.logic_detail_controller = LogicDetailController(self.logic_detail_widget)
        self.basic_features_layout.addWidget(self.logic_detail_widget)
        
        # 로직 생성 위젯과 컨트롤러
        self.logic_maker_widget = LogicMakerWidget()
        self.logic_maker_controller = LogicMakerController(self.logic_maker_widget)
        self.basic_features_layout.addWidget(self.logic_maker_widget)
        
        self.main_layout.addLayout(self.basic_features_layout)
        
    def init_advanced_features(self):
        """고급 기능 영역 초기화"""
        self.advanced_widget = AdvancedWidget()
        self.advanced_features_layout.addWidget(self.advanced_widget)
        self.main_layout.addLayout(self.advanced_features_layout)
        
    def init_log_features(self):
        """로그 영역 초기화"""
        self.log_widget = LogWidget()
        self.log_layout.addWidget(self.log_widget)
        self.main_layout.addLayout(self.log_layout)
        
    def _setup_connections(self):
        """컴포넌트 간 시그널/슬롯 연결 설정"""
        # 로직 리스트와 상세 정보 연결
        self.logic_list_widget.logic_selected.connect(self.logic_detail_controller.on_logic_selected)
        
        # 로직 생성과 리스트 연결
        self.logic_maker_widget.logic_created.connect(self.logic_list_controller.on_logic_created)
        
        # 고급 기능과 로직 상세 정보 연결
        self.advanced_widget.advanced_action.connect(self.logic_detail_controller.on_advanced_action)
