from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QLineEdit, QFrame, QListWidget,
                           QListWidgetItem, QTextEdit, QSizePolicy, QScrollArea,
                           QMessageBox)
from PySide6.QtCore import Qt, QPoint, QSize, QSettings
from PySide6.QtGui import QFont
import sys

from BE.ui.components.title.title_widget import TitleWidget
from BE.ui.components.logic_list.logic_list_widget import LogicListWidget
from BE.ui.components.logic_list.logic_list_controller import LogicListController
from BE.ui.components.logic_detail.logic_detail_widget import LogicDetailWidget
from BE.ui.components.logic_detail.logic_detail_controller import LogicDetailController
from BE.ui.components.logic_maker.logic_maker_widget import LogicMakerWidget
from BE.ui.components.logic_maker.logic_maker_controller import LogicMakerController
from BE.ui.components.logic_operation.logic_operation_controller import LogicOperationController
from BE.ui.components.logic_operation.logic_operation_widget import LogicOperationWidget
from BE.ui.components.advanced.advanced_widget import AdvancedWidget
from BE.ui.components.log.log_widget import LogWidget
from BE.settings.settings_manager import SettingsManager
from BE.ui.utils.error_handler import ErrorHandler

from BE.ui.constants.dimensions import (MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, BASIC_SECTION_HEIGHT,
                               MIDDLE_SPACE, ADVANCED_SECTION_HEIGHT)

class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        
        # 전역 예외 처리기 설정
        self.error_handler = ErrorHandler()
        
        self.init_ui()
        self._setup_connections()  # 시그널/슬롯 연결 설정
        self._load_window_settings()
        
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
        
        # 로직 동작 온오프 위젯
        self.logic_operation_widget = LogicOperationWidget()
        self.logic_operation_controller = LogicOperationController(self.logic_operation_widget)
        self.logic_operation_widget.log_message.connect(self._append_log)  # 로그 메시지 연결
        self.main_layout.addWidget(self.logic_operation_widget)
        
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
        
        # 로직 메이커
        self.logic_maker_widget = LogicMakerWidget()
        self.logic_maker_controller = LogicMakerController(self.logic_maker_widget)
        self.basic_features_layout.addWidget(self.logic_maker_widget)
        
        # 시그널 연결
        self.logic_maker_widget.record_mode.connect(self._handle_record_mode)
        
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
        # 전역 에러 핸들러 연결
        self.error_handler.error_occurred.connect(self._append_log)
        
        # 로직 리스트와 상세 정보 연결
        self.logic_list_widget.logic_selected.connect(self.logic_detail_controller.on_logic_selected)
        self.logic_list_widget.edit_logic.connect(self.logic_detail_widget.load_logic)
        
        # 로직 저장/수정 시그널 연결
        self.logic_detail_widget.logic_saved.connect(self.logic_list_widget.on_logic_saved)
        self.logic_detail_widget.logic_updated.connect(self.logic_list_widget.on_logic_updated)
        
        # 로그 메시지 연결
        self.logic_list_widget.log_message.connect(self._append_log)
        self.logic_detail_widget.log_message.connect(self._append_log)
        self.logic_maker_widget.log_message.connect(self._append_log)
        
        # 고급 기능과 로직 상세 정보 연결
        self.advanced_widget.advanced_action.connect(self.logic_detail_controller.on_advanced_action)
        
        # 로직 메이커 시그널 연결
        self.logic_maker_widget.key_input.connect(self._on_key_input)
        self.logic_maker_widget.mouse_input.connect(self._on_mouse_input)
        self.logic_maker_widget.delay_input.connect(self._on_delay_input)
        
    def _handle_record_mode(self):
        # TODO: Implement record mode handling
        pass

    def _append_log(self, message):
        """로그 메시지 추가"""
        self.log_widget.append(message)
        
    def _on_key_input(self, key_info):
        """키 입력이 추가되었을 때 호출"""
        # 키 정보를 문자열로 변환
        key_text = key_info.get('display_text', '')  # 이벤트 타입이 포함된 텍스트 사용
        modifiers = key_info.get('modifiers', 0)
        modifier_text = ""
        
        if modifiers & Qt.ControlModifier:
            modifier_text += "Ctrl+"
        if modifiers & Qt.ShiftModifier:
            modifier_text += "Shift+"
        if modifiers & Qt.AltModifier:
            modifier_text += "Alt+"
            
        display_text = f"키 입력: {modifier_text}{key_text}"
        self.logic_detail_widget.add_item(display_text)
        
    def _on_mouse_input(self, mouse_info):
        """마우스 입력이 추가되었을 때 호출"""
        # TODO: 마우스 입력 처리 로직 구현
        pass
        
    def _on_delay_input(self, delay_info):
        """지연시간이 추가되었을 때 호출"""
        self.logic_detail_widget.add_item(delay_info)
        
    def _on_record_mode(self, is_recording):
        """기록 모드가 토글되었을 때 호출"""
        # TODO: 기록 모드 처리 로직 구현
        pass

    def _handle_edit_logic(self, logic_name, items):
        """로직 수정 처리"""
        if self.logic_detail_widget.has_items():
            # 확인 모달 표시
            reply = QMessageBox.question(
                self,
                "로직 수정",
                "현재 작성 중인 로직이 있습니다. 덮어쓰시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                self._append_log("로직 수정이 취소되었습니다")
                return
        
        # 로직 데이터 로드
        self.logic_detail_widget.load_logic(logic_name, items)
        self._append_log(f"로직 '{logic_name}'을(를) 수정합니다")

    def _load_window_settings(self):
        """윈도우 설정 로드"""
        settings = self.settings_manager.get_window_settings()
        position = settings["position"]
        size = settings["size"]
        
        self.resize(size["width"], size["height"])
        self.move(position["x"], position["y"])
        
    def closeEvent(self, event):
        """윈도우가 닫힐 때 호출되는 이벤트 핸들러"""
        # 현재 윈도우 위치와 크기 저장
        position = self.pos()
        size = self.size()
        
        self.settings_manager.set_window_position(position.x(), position.y())
        self.settings_manager.set_window_size(size.width(), size.height())
        
        super().closeEvent(event)
