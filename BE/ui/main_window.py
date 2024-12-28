from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QLineEdit, QFrame, QListWidget,
                           QListWidgetItem, QTextEdit, QSizePolicy, QScrollArea,
                           QMessageBox)
from PySide6.QtCore import Qt, QPoint, QSize, QSettings
from PySide6.QtGui import QFont
import sys
import traceback

from BE.ui.components.logic_list.logic_list_widget import LogicListWidget
from BE.ui.components.logic_list.logic_list_controller import LogicListController
from BE.ui.components.logic_detail.logic_detail_widget import LogicDetailWidget
from BE.ui.components.logic_detail.logic_detail_controller import LogicDetailController
from BE.ui.components.logic_maker.logic_maker_widget import LogicMakerToolWidget
from BE.ui.components.logic_maker.logic_maker_controller import LogicMakerController
from BE.ui.components.logic_operation.logic_operation_controller import LogicOperationController
from BE.ui.components.logic_operation.logic_operation_widget import LogicOperationWidget
from BE.ui.components.advanced.advanced_widget import AdvancedWidget
from BE.ui.components.advanced.advanced_controller import AdvancedController
from BE.ui.components.log.log_widget import LogWidget
from BE.settings.settings_manager import SettingsManager
from BE.ui.utils.error_handler import ErrorHandler
from BE.logic.logic_manager import LogicManager
from BE.logic.logic_executor import LogicExecutor
from BE.ui.components.process.process_manager import ProcessManager

from BE.ui.constants.dimensions import (MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, BASIC_SECTION_HEIGHT,
                               MIDDLE_SPACE, ADVANCED_SECTION_HEIGHT)

class MainWindow(QMainWindow):
    """메인 윈도우 클래스"""
    
    def __init__(self):
        super().__init__()
        self.settings_manager = SettingsManager()
        
        # 전역 예외 처리기 설정
        self.error_handler = ErrorHandler()
        
        # 프로세스 매니저 초기화
        self.process_manager = ProcessManager()
        
        # 로직 관리자와 실행기 초기화
        self.logic_manager = LogicManager(self.settings_manager)
        self.logic_executor = LogicExecutor(self.process_manager, self.logic_manager)
        
        self.init_ui()
        self._setup_connections()  # 시그널/슬롯 연결 설정
        self._load_window_settings()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("또끼")        
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
        # 로직 동작 온오프 위젯
        self.logic_operation_widget = LogicOperationWidget()
        self.logic_operation_widget.set_logic_executor(self.logic_executor)  # set_logic_executor 메서드 사용
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
        self.logic_maker_widget = LogicMakerToolWidget()
        self.logic_maker_controller = LogicMakerController(self.logic_maker_widget)
        
        # 로직 메이커에 저장된 로직 목록 전달
        self.logic_maker_widget.update_saved_logics(self.logic_list_widget.saved_logics)
        
        self.basic_features_layout.addWidget(self.logic_maker_widget)
        
        # 시그널 연결
        self.logic_maker_widget.record_mode.connect(self._handle_record_mode)
        
        self.main_layout.addLayout(self.basic_features_layout)
        
    def init_advanced_features(self):
        """고급 기능 영역 초기화"""
        self.advanced_widget = AdvancedWidget()
        # 초기 로직 목록 전달
        self.advanced_widget.update_saved_logics(self.logic_list_widget.saved_logics)
        self.advanced_features_layout.addWidget(self.advanced_widget)
        self.main_layout.addLayout(self.advanced_features_layout)
        
        # AdvancedController 초기화 및 연결
        self.advanced_controller = AdvancedController(
            process_manager=self.process_manager,
            logic_manager=self.logic_manager
        )
        self.advanced_controller.widget = self.advanced_widget
        
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
        self.logic_list_widget.edit_logic.connect(self._handle_edit_logic)
        self.logic_list_widget.item_deleted.connect(self._on_logic_deleted)
        
        # 로직 저장/수정 시그널 연결
        self.logic_detail_widget.logic_saved.connect(self.logic_list_widget.on_logic_saved)
        self.logic_detail_widget.logic_updated.connect(self.logic_list_widget.on_logic_updated)
        self.logic_detail_widget.logic_saved.connect(self._on_logic_saved)
        self.logic_detail_widget.logic_updated.connect(self._on_logic_updated)
        
        # 로그 메시지 연결
        self.logic_list_widget.log_message.connect(self._append_log)
        self.logic_detail_widget.log_message.connect(self._append_log)
        self.logic_maker_widget.log_message.connect(self._append_log)
        self.logic_operation_widget.log_message.connect(self._append_log)  # _append_log를 통해 로그 추가
        
        # 고급 기능과 로직 상세 정보 연결
        self.advanced_widget.advanced_action.connect(self.logic_detail_controller.on_advanced_action)
        
        # 로직 메이커 시그널 연결
        self.logic_maker_widget.key_input.connect(self._on_key_input)
        self.logic_maker_widget.mouse_input.connect(self._on_mouse_input)
        self.logic_maker_widget.delay_input.connect(self._on_delay_input)
        self.logic_maker_widget.add_logic.connect(self._on_add_logic)  # 로직 추가 시그널 연결
        self.logic_maker_widget.wait_click_input.connect(self._on_wait_click_input)  # 클릭 대기 시그널 연결
        self.logic_maker_widget.item_added.connect(self._on_item_added)  # 아이템 추가 시그널 연결
        
        # 로직 실행 관련 시그널 연결
        self.logic_operation_widget.operation_toggled.connect(self._on_logic_operation_toggled)
        self.logic_operation_widget.process_selected.connect(self._on_process_selected)
        self.logic_operation_widget.process_reset.connect(self._on_process_reset)
        self.logic_executor.execution_started.connect(lambda: self._append_log("로직 실행이 시작되었습니다"))
        self.logic_executor.execution_finished.connect(lambda: self._append_log("로직 실행이 완료되었습니다"))
        self.logic_executor.execution_error.connect(lambda msg: self._append_log(f"로직 실행 중 오류 발생: {msg}"))
        #self.logic_executor.execution_state_changed.connect(lambda state: self._append_log(f"실행 상태 변경: {state}"))  # 상태 변경 로깅
        self.logic_executor.log_message.connect(self.log_widget.append)
    
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
        """마우스 입력 정보를 받아서 처리"""
        try:
            # 로그 메시지 출력
            if isinstance(mouse_info, dict):
                display_text = mouse_info.get('display_text', '')
                self.log_widget.append(f"(main_window--_on_mouse_input)마우스 입력이 추가되었습니다: {display_text}")
                
                # 로직 상세 위젯에 마우스 입력 추가
                if self.logic_detail_widget:
                    self.logic_detail_widget.add_item(mouse_info)
            else:
                self.log_widget.append(f"[경고] 잘못된 형식의 마우스 입력 데이터가 전달되었습니다: {mouse_info}")
                
        except Exception as e:
            import traceback
            self.log_widget.append(f"마우스 입력 처리 중 오류 발생: {str(e)}")
            self.log_widget.append(f"스택 트레이스:\n{traceback.format_exc()}")
        
    def _on_delay_input(self, delay_info):
        """지연시간이 추가되었을 때 호출"""
        self.logic_detail_widget.add_item(delay_info)
        
    def _on_record_mode(self, is_recording):
        """기록 모드가 토글되었을 때 호출"""
        # TODO: 기록 모드 처리 로직 구현
        pass

    def _handle_edit_logic(self, logic_info):
        """로직 불러오기 처리"""
        if self.logic_detail_widget.has_items():
            # 확인 모달 시그널
            reply = QMessageBox.question(
                self,
                "로직 불러오기",
                "현재 작성 중인 로직이 있습니다. 덮어쓰시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                self._append_log("로직 불러오기가 취소되었습니다")
                return
        
        # 로직 데이터 로드
        self.logic_detail_widget.load_logic(logic_info)
        self._append_log(f"로직 '{logic_info['name']}'를(를) 수정합니다")

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

    def _on_logic_operation_toggled(self, is_enabled):
        """로직 동작 체크박스 상태가 변경되었을 때 호출"""
        if is_enabled:
            self.logic_executor.start_monitoring()
            self.advanced_controller.set_monitoring_enabled(True)  # 게이지 모니터링 시작
            self._append_log("로직 동작이 활성화되었습니다")
        else:
            self.logic_executor.stop_monitoring()
            self.advanced_controller.set_monitoring_enabled(False)  # 게이지 모니터링 중지
            self._append_log("로직 동작이 비활성화되었습니다")
    
    def _on_logic_saved(self, logic_info):
        """로직이 저장되었을 때 호출"""
        self.logic_manager.load_logic(logic_info['name'])
        # 로직 메이커와 고급 기능 위젯의 저장된 로직 목록 업데이트
        self.logic_maker_widget.update_saved_logics(self.logic_list_widget.saved_logics)
        self.advanced_widget.update_saved_logics(self.logic_list_widget.saved_logics)
        # 로직 구성 영역 초기화
        self.logic_detail_widget.clear_all()
    
    def _on_logic_updated(self, original_name, logic_info):
        """로직이 수정되었을 때 호출"""
        self.logic_manager.load_logic(logic_info['name'])
        # 로직 메이커와 고급 기능 위젯의 저장된 로직 목록 업데이트
        self.logic_maker_widget.update_saved_logics(self.logic_list_widget.saved_logics)
        self.advanced_widget.update_saved_logics(self.logic_list_widget.saved_logics)

    def _on_logic_deleted(self, logic_name):
        """로직이 삭제되었을 때 호출"""
        # 로직 매니저에서 로직 제거
        self.logic_manager.remove_logic(logic_name)
        # 로직 메이커와 고급 기능 위젯의 ��장된 로직 목록 업데이트
        self.logic_maker_widget.update_saved_logics(self.logic_list_widget.saved_logics)
        self.advanced_widget.update_saved_logics(self.logic_list_widget.saved_logics)
        # 로직 구성 영역 초기화
        self.logic_detail_widget.clear_all()

    def _on_process_selected(self, process_info):
        """프로세스가 선택되었을 때 호출"""
        self.process_manager.set_selected_process(process_info)
        self.advanced_controller.set_target_process(process_info)
        self._append_log(f"프로세스를 선택했습니다: {process_info}")
    
    def _on_process_reset(self):
        """프로세스가 초기화되었을 때 호출"""
        self.process_manager.set_selected_process(None)
        self.advanced_controller.set_target_process(None)
        self._append_log("프로세스 선택이 초기화되었습니다")

    def _on_add_logic(self, logic_name):
        """로직 메이커에서 로직을 추가할 때 호출"""
        if logic_name in self.logic_list_widget.saved_logics:
            # 로직 정보에서 이름을 가져와서 아이템으로 추가
            logic_info = self.logic_list_widget.saved_logics[logic_name]
            display_name = logic_info.get('name', logic_name)
            self.logic_detail_widget.add_item(display_name)
            self._append_log(f"로직 '{display_name}'이(가) 추가되었습니다")

    def _on_wait_click_input(self, wait_click_info):
        """클릭 대기 입력이 추가되었을 때 호출"""
        try:
            display_text = wait_click_info.get('display_text', '')
            self.log_widget.append(f"클릭 대기 아이템이 추가되었습니다: {display_text}")
            
            # 로직 상세 위젯에 클릭 대기 입력 추가
            if self.logic_detail_widget:
                self.logic_detail_widget.add_item(wait_click_info)
                
        except Exception as e:
            self.log_widget.append(f"[경고] 클릭 대기 입력 처리 중 오류 발생: {str(e)}")

    def _on_item_added(self, item_info):
        """아이템이 추가되었을 때 호출"""
        if isinstance(item_info, dict) and item_info.get('type') == 'write_text':
            # 텍스트 입력인 경우 깔끔하게 표시
            text = item_info.get('text', '')
            display_text = f"텍스트 입력: {text}"
            item_info['display_text'] = display_text
            self.logic_detail_widget.add_item(item_info)
        else:
            # 다른 타입의 아이템은 그대로 전달
            self.logic_detail_widget.add_item(item_info)
