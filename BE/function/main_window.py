from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QPushButton, QLabel, QLineEdit, QFrame, QListWidget,
                           QListWidgetItem, QTextEdit, QSizePolicy, QScrollArea,
                           QMessageBox)
from PySide6.QtCore import Qt, QPoint, QSize, QSettings
from PySide6.QtGui import QFont
import sys
import traceback
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_widget import EnteredKeyInfoWidget
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog
from BE.function.make_logic.logic_list.logic_list_widget import LogicListWidget
from BE.function.make_logic.logic_list.logic_list_controller import LogicListController
from BE.function.make_logic.logic_detail.logic_detail_widget import LogicDetailWidget
from BE.function.make_logic.logic_detail.logic_detail_controller import LogicDetailController
from BE.function.make_logic.logic_maker_tool.logic_maker_tool_widget import LogicMakerToolWidget
from BE.function.make_logic.logic_maker_tool.logic_maker_tool_controller import LogicMakerController
from BE.function.make_logic.logic_operation.logic_operation_controller import LogicOperationController
from BE.function.make_logic.logic_operation.logic_operation_widget import LogicOperationWidget
from BE.log.log_widget import LogWidget
from BE.settings.settings_data_manager import SettingsManager
from BE.function._common_components.error_handler import ErrorHandler
from BE.function.manage_logic.logic_manager import LogicManager
from BE.function.execute_logic.logic_executor import LogicExecutor
from BE.function._common_components.window_process_handler import ProcessManager
from BE.function.constants.dimensions import (MAIN_WINDOW_WIDTH, MAIN_WINDOW_HEIGHT, BASIC_SECTION_HEIGHT,
                               MIDDLE_SPACE)
from BE.function.etc_function.countdown.UI.etc_function_widget import EtcFunctionWidget
from BE.function.etc_function.countdown.Controller.countdown_controller__input_sequence import CountdownControllerInputSequence
from BE.function._common_components.modal.entered_key_info_modal.keyboard_hook_handler import KeyboardHook
import logging
from BE.log.manager.base_log_manager import BaseLogManager

class MainWindow(QMainWindow):
    """메인 윈도우 클래스
    
    애플리케이션의 메인 윈도우를 구성하는 클래스입니다.
    모든 UI 컴포넌트들을 관리하고 이들 간의 상호작용을 조정합니다.
    
    Attributes:
        settings_manager (SettingsManager): 설정 관리자
        error_handler (ErrorHandler): 전역 예외 처리기
        process_manager (ProcessManager): 프로세스 관리자
        logic_manager (LogicManager): 로직 관리자
        logic_executor (LogicExecutor): 로직 실행기
        keyboard_hook (KeyboardHook): 키보드 입력 후킹 관리자
        
    Components:
        logic_operation_widget (LogicOperationWidget): 로직 동작 제어 위젯
        logic_list_widget (LogicListWidget): 로직 목록 위젯
        logic_detail_widget (LogicDetailWidget): 로직 상세 정보 위젯
        logic_maker_tool_widget (LogicMakerToolWidget): 로직 생성 도구 위젯
        etc_function_widget (EtcFunctionWidget): 기타 기능 위젯
        log_widget (LogWidget): 로그 표시 위젯
    """
    
    def __init__(self):
        """메인 윈도우 초기화
        
        초기화 프로세스:
        1. 기본 설정 초기화
           - 설정 매니저
           - 전역 예외 처리기
           - 프로세스 매니저
           - 로직 관리자와 실행기
           - 키보드 훅
           
        2. UI 초기화
           - 기본 UI 구성
           - 컴포넌트 초기화
           - 시그널/슬롯 연결
           
        3. 윈도우 설정 로드
        """
        super().__init__()
        self.settings_manager = SettingsManager()
        
        # 전역 예외 처리기 설정
        self.error_handler = ErrorHandler()
        
        # 프로세스 매니저 초기화
        self.process_manager = ProcessManager()
        
        # 로직 관리자와 실행기 초기화
        self.logic_manager = LogicManager(self.settings_manager)
        self.logic_executor = LogicExecutor(self.process_manager, self.logic_manager)
        
        # 키보드 훅 초기화
        self.keyboard_hook = KeyboardHook()
        self.keyboard_hook.start()
        
        # 모달 로그 매니저 초기화
        self.modal_log_manager = BaseLogManager.instance()
        
        # 로그 위젯 초기화
        self.log_widget = LogWidget()
        
        self.init_ui()
        self._setup_connections()  # 시그널/슬롯 연결 설정
        self._load_window_settings()
        
    def init_ui(self):
        """UI 초기화
        
        메인 윈도우의 기본 UI를 구성합니다.
        
        구성 프로세스:
        1. 윈도우 기본 설정
           - 타이틀 설정
           - 크기 설정
           
        2. 스크롤 영역 설정
           - 수직 스크롤바 자동 표시
           - 수평 스크롤바 숨김
           
        3. 메인 위젯 구성
           - 레이아웃 초기화
           - UI 컴포넌트 초기화
           - 스크롤 영역에 추가
        """
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
        """레이아웃 초기화
        
        메인 윈도우의 레이아웃 구조를 설정합니다.
        
        레이아웃 구조:
        1. 메인 레이아웃 (QVBoxLayout)
           - 전체 UI 컴포넌트를 수직으로 배치
           - 컴포넌트 간 간격 설정
           
        2. 기본 기능 영역 레이아웃 (QHBoxLayout)
           - 로직 관련 주요 기능들을 수평으로 배치
           
        3. 로그 영역 레이아웃 (QHBoxLayout)
           - 로그 위젯을 위한 영역
        """
        # 메인 레이아웃
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(MIDDLE_SPACE)
        
        # 기본 기능 영역 레이아웃
        self.basic_features_layout = QHBoxLayout()
        self.basic_features_layout.setSpacing(0)
        
        # 로그 영역 레이아웃
        self.log_layout = QHBoxLayout()
        self.log_layout.setSpacing(0)
    
    def init_components(self):
        """UI 컴포넌트 초기화
        
        메인 윈도우의 각 UI 컴포넌트를 초기화하고 배치합니다.
        
        초기화되는 컴포넌트:
        1. 로직 동작 제어 위젯
           - 로직 실행기 설정
           - 컨트롤러 연결
           - 로그 메시지 연결
           
        2. 기본 기능 영역
           - 로직 리스트
           - 로직 상세 정보
           - 로직 메이커
           
        3. 기타 기능 위젯
           - 카운트다운 컨트롤러 설정
           - 로그 메시지 연결
           
        4. 로그 영역
           - 로그 위젯 초기화
        """
        # 로직 동작 허용 여부 온오프 위젯
        self.logic_operation_widget = LogicOperationWidget()
        self.logic_operation_widget.set_logic_executor(self.logic_executor)  # set_logic_executor 메서드 사용
        self.logic_operation_controller = LogicOperationController(self.logic_operation_widget)
        self.main_layout.addWidget(self.logic_operation_widget)
        
        # 기본 기능 영역
        self.init_basic_features()
        
        # 기타 기능 위젯
        self.etc_function_widget = EtcFunctionWidget()
        self.countdown_controller__input_sequence = CountdownControllerInputSequence(self.etc_function_widget)
        self.main_layout.addWidget(self.etc_function_widget)
        
        # 로그 영역
        self.init_log_features()
        
    def init_basic_features(self):
        """기본 기능 영역 초기화
        
        로직 관련 주요 기능들을 초기화하고 배치합니다.
        
        초기화되는 기능:
        1. 로직 리스트
           - 위젯과 컨트롤러 생성
           - 레이아웃에 추가
           
        2. 로직 상세 정보
           - 위젯과 컨트롤러 생성
           - 레이아웃에 추가
           
        3. 로직 메이커
           - 위젯과 컨트롤러 생성
           - 저장된 로직 목록 전달
           - 레이아웃에 추가
           - 시그널 연결
        """
        # 로직 리스트 위젯과 컨트롤러
        self.logic_list_widget = LogicListWidget()
        self.logic_list_controller = LogicListController(self.logic_list_widget)
        self.basic_features_layout.addWidget(self.logic_list_widget)
        
        # 로직 상세 정보 위젯과 컨트롤러
        self.logic_detail_widget = LogicDetailWidget()
        self.logic_detail_controller = LogicDetailController(self.logic_detail_widget)
        self.basic_features_layout.addWidget(self.logic_detail_widget)
        
        # 로직 메이커
        self.logic_maker_tool_widget = LogicMakerToolWidget()
        self.logic_maker_tool_controller = LogicMakerController(self.logic_maker_tool_widget)
        
        # 로직 메이커에 저장된 로직 목록 전달
        self.logic_maker_tool_widget.update_saved_logics(self.logic_list_controller.get_saved_logics())
        
        self.basic_features_layout.addWidget(self.logic_maker_tool_widget)
        
        # 시그널 연결
        self.logic_maker_tool_widget.record_mode.connect(self._handle_record_mode)
        
        self.main_layout.addLayout(self.basic_features_layout)
        
    def init_log_features(self):
        """로그 영역 초기화
        
        로그 표시를 위한 UI를 초기화합니다.
        
        구성:
        - 로그 위젯 생성
        - 레이아웃에 추가
        """
        self.log_layout.addWidget(self.log_widget)
        self.main_layout.addLayout(self.log_layout)
        
    def _setup_connections(self):
        """컴포넌트 간 시그널/슬롯 연결 설정
        
        각 컴포넌트 간의 상호작용을 위한 시그널과 슬롯을 연결합니다.
        
        연결되는 시그널:
        1. 에러 처리
           - 전역 에러 핸들러 -> 로그
           
        2. 키보드 입력
           - 키보드 훅 -> 카운트다운 컨트롤러
           
        3. 로직 동작 제어
           - 동작 상태 변경 -> 기타 기능 위젯
           
        4. 프로세스 관리
           - 프로세스 선택 -> 카운트다운 컨트롤러
           
        5. 로직 관리
           - 로직 선택/편집/삭제
           - 로직 저장/수정
           
        6. 로그 메시지
           - 각 컴포넌트의 로그 -> 로그 위젯
           
        7. 로직 메이커
           - 키/마우스 입력
           - 로직 추가/수정
           
        8. 로직 실행
           - 실행 상태 변경
           - 오류 발생
        """
        # 전역 에러 핸들러 연결
        self.error_handler.error_occurred.connect(lambda msg: self.modal_log_manager.log(
            message=msg,
            level="ERROR",
            modal_name="시스템",
            print_to_terminal=True
        ))
        
        # 키보드 훅 시그널을 CountdownControllerInputSequence에 연결
        self.keyboard_hook.key_pressed.connect(self.countdown_controller__input_sequence._on_key_pressed)
        self.keyboard_hook.key_released.connect(self.countdown_controller__input_sequence._on_key_released)
        
        # 로직 동작 허용 여부 변경 시 기타 기능 위젯에도 전달
        self.logic_operation_widget.operation_toggled.connect(self.etc_function_widget.set_logic_enabled)
        
        # 프로세스 선택 시 기타 기능 컨트롤러에도 전달
        self.process_manager.process_selected.connect(self.countdown_controller__input_sequence.process_manager.set_selected_process)
        
        # 로직 리스트와 상세 정보 연결
        self.logic_list_widget.logic_selected.connect(self._handle_edit_logic)
        self.logic_list_widget.edit_logic.connect(self._handle_edit_logic)
        self.logic_list_widget.logic_delete_requested.connect(self._on_logic_deleted)
        
        # 로직 저장/수정 시그널 연결
        self.logic_detail_widget.logic_saved.connect(self.logic_list_controller.on_logic_saved)
        self.logic_detail_widget.logic_updated.connect(self.logic_list_controller.on_logic_updated)
        self.logic_detail_widget.logic_saved.connect(self._on_logic_saved)
        self.logic_detail_widget.logic_updated.connect(self._on_logic_updated)
        
        # 로직 메이커 시그널 연결
        self.logic_maker_tool_widget.item_added.connect(self._on_item_added)  # 아이템 추가 시그널 연결
        self.logic_maker_tool_widget.mouse_input.connect(self._on_mouse_input)
        self.logic_maker_tool_widget.delay_input.connect(self._on_delay_input)
        self.logic_maker_tool_widget.add_logic.connect(self._on_add_logic)  # 로직 추가 시그널 연결
        self.logic_maker_tool_widget.wait_click_input.connect(self._on_wait_click_input)
        
        # 로직 실행 관련 시그널 연결
        self.logic_operation_widget.operation_toggled.connect(self._on_logic_operation_toggled)
        self.logic_operation_widget.process_selected.connect(self._on_process_selected)
        self.logic_operation_widget.process_reset.connect(self._on_process_reset)
        
        # 로직 실행기 시그널 연결
        self.logic_executor.execution_started.connect(lambda: self.modal_log_manager.log(
            message="로직 실행이 시작되었습니다",
            level="INFO",
            modal_name="로직실행",
            include_time=True
        ))
        
        self.logic_executor.execution_finished.connect(lambda: self.modal_log_manager.log(
            message="로직 실행이 완료되었습니다",
            level="INFO",
            modal_name="로직실행",
            include_time=True
        ))
        
        self.logic_executor.execution_error.connect(lambda msg: self.modal_log_manager.log(
            message=f"로직 실행 중 오류 발생: {msg}",
            level="ERROR",
            modal_name="로직실행",
            include_time=True,
            print_to_terminal=True
        ))
    
    def _handle_record_mode(self):
        """녹화 모드 처리
        
        TODO: 녹화 모드 기능 구현
        """
        pass

    def _on_mouse_input(self, mouse_info):
        """마우스 입력 정보 처리
        
        LogicMakerToolWidget에서 전달된 마우스 입력 정보를 처리하고 표시합니다.
        
        Args:
            mouse_info (dict): 마우스 입력 정보
                - x (int): X 좌표
                - y (int): Y 좌표
                - button (str): 클릭된 버튼 ('left', 'right', 'middle')
                - action (str): 동작 유형 ('press', 'release', 'move')
                
        프로세스:
        1. 입력 정보 유효성 검사
        2. 표시 형식으로 변환
        3. LogicDetailWidget에 추가
        """
        try:
            # 로그 메시지 출력
            if isinstance(mouse_info, dict):
                display_text = mouse_info.get('display_text', '')
                self.modal_log_manager.log(
                    message=f"마우스 입력이 추가되었습니다: {display_text}",
                    level="INFO",
                    modal_name="로직상세"
                )
                
                # 로직 상세 위젯에 마우스 입력 추가
                if self.logic_detail_widget:
                    self.logic_detail_widget.add_item(mouse_info)
            else:
                self.modal_log_manager.log(
                    message=f"잘못된 형식의 마우스 입력 데이터가 전달되었습니다: {mouse_info}",
                    level="WARNING",
                    modal_name="로직상세"
                )
                
        except Exception as e:
            self.modal_log_manager.log(
                message=f"마우스 입력 처리 중 오류 발생: {str(e)}\n{traceback.format_exc()}",
                level="ERROR",
                modal_name="로직상세",
                print_to_terminal=True
            )

    def _on_delay_input(self, delay_info):
        """지연 시간 입력 처리
        
        LogicMakerToolWidget에서 전달된 지연 시간 정보를 처리합니다.
        
        Args:
            delay_info (dict): 지연 시간 정보
                - duration (float): 지연 시간(초)
                - type (str): 지연 유형
                
        프로세스:
        1. 지연 정보를 표시 형식으로 변환
        2. LogicDetailWidget에 추가
        """
        self.logic_detail_widget.add_item(delay_info)
        
    def _on_record_mode(self, is_recording):
        """기록 모드가 토글되었을 때 호출"""
        # TODO: 기록 모드 처리 로직 구현
        pass

    def _handle_edit_logic(self, logic_info):
        """로직 편집 처리
        
        로직 편집이 요청되었을 때 처리합니다.
        
        Args:
            logic_info (dict): 로직 정보
                - id (str): 로직 ID
                - name (str): 로직 이름
                - items (list): 로직 아이템 목록
                
        프로세스:
        1. 로직 정보 검증
        2. LogicDetailWidget에 로직 정보 전달
        3. 편집 모드 활성화
        """
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
                self.modal_log_manager.log(
                    message="로직 불러오기가 취소되었습니다",
                    level="INFO",
                    modal_name="로직상세"
                )
                return
        
        # logic_info가 문자열(로직 이름)인 경우 로직 정보를 가져옴
        if isinstance(logic_info, str):
            logic_name = logic_info
            logic_info = self.logic_list_controller.get_logic_by_name(logic_name)
            if not logic_info:
                self.modal_log_manager.log(
                    message=f"로직 '{logic_name}'을(를) 찾을 수 없습니다",
                    level="ERROR",
                    modal_name="로직상세"
                )
                return
        
        # 로직 데이터 로드
        self.logic_detail_widget.load_logic(logic_info)
        self.modal_log_manager.log(
            message=f"로직 '{logic_info.get('name', '')}'를(를) 수정합니다",
            level="INFO",
            modal_name="로직상세"
        )

    def _load_window_settings(self):
        """윈도우 설정 로드
        
        저장된 윈도우 위치와 크기를 로드하고 적용합니다.
        
        프로세스:
        1. 설정 파일에서 윈도우 정보 로드
        2. 유효성 검사
        3. 윈도우에 적용
        """
        settings = self.settings_manager.get_window_settings()
        position = settings["position"]
        size = settings["size"]
        
        self.resize(size["width"], size["height"])
        self.move(position["x"], position["y"])
        
    def closeEvent(self, event):
        """윈도우 종료 이벤트 처리
        
        윈도우가 종료될 때 필요한 정리 작업을 수행합니다.
        
        Args:
            event (QCloseEvent): 종료 이벤트
            
        프로세스:
        1. 현재 윈도우 상태 저장
        2. 키보드 훅 정리
        3. 실행 중인 작업 정리
        4. 이벤트 수락
        """
        try:
            # 윈도우 위치와 크기 저장
            settings = QSettings()
            settings.setValue("geometry", self.geometry())
            
            # 키보드 훅 정리
            if hasattr(self, 'keyboard_hook'):
                self.keyboard_hook.stop()
            
            # 프로세스 체크 타이머 정리
            if hasattr(self.countdown_controller__input_sequence, 'process_check_timer'):
                self.countdown_controller__input_sequence.process_check_timer.stop()
            
            event.accept()
            
        except Exception as e:
            self.modal_log_manager.log(
                message=f"윈도우 종료 중 오류 발생: {str(e)}",
                level="ERROR",
                modal_name="시스템",
                print_to_terminal=True
            )
            event.accept()

    def _on_logic_operation_toggled(self, enabled):
        """로직 동작 상태 변경 처리
        
        로직 실행 활성화/비활성화 상태가 변경되었을 때 처리합니다.
        
        Args:
            enabled (bool): 활성화 여부
            
        프로세스:
        1. 로직 실행기 상태 업데이트
        2. UI 상태 업데이트
        3. 로그 메시지 출력
        """
        if enabled:
            self.logic_executor.start_monitoring()
            self.modal_log_manager.log(
                message="로직 동작 허용 여부가 허용 상태로 변경되었습니다<br>",
                level="INFO",
                modal_name="로직동작"
            )
        else:
            self.logic_executor.stop_monitoring()
            self.modal_log_manager.log(
                message="로직 동작 허용 여부가 불허용 상태로 변경되었습니다<br>",
                level="INFO",
                modal_name="로직동작"
            )
    
    def _on_logic_saved(self, logic_info):
        """로직 저장 완료 처리
        
        새로운 로직이 저장되었을 때 처리합니다.
        
        Args:
            logic_info (dict): 저장된 로직 정보
                - id (str): 로직 ID
                - name (str): 로직 이름
                - items (list): 로직 아이템 목록
                
        프로세스:
        1. 설정 파일에 저장
        2. UI 업데이트
        3. 로그 메시지 출력
        """
        # 로직 리스트 컨트롤러를 통해 저장된 로직 정보 가져오기
        saved_logics = self.logic_list_controller.get_saved_logics()
        self.logic_maker_tool_widget.update_saved_logics(saved_logics)
        # 로직 정보 초기화
        self.logic_detail_widget.clear_all()
        self.modal_log_manager.log(
            message=f"로직 '{logic_info.get('name', '')}'이(가) 저장되었습니다",
            level="INFO",
            modal_name="로직상세"
        )
    
    def _on_logic_updated(self, logic_info):
        """로직 수정 완료 처리
        
        기존 로직이 수정되었을 때 처리합니다.
        
        Args:
            logic_info (dict): 수정된 로직 정보
                - id (str): 로직 ID
                - name (str): 로직 이름
                - items (list): 로직 아이템 목록
                
        프로세스:
        1. 설정 파일 업데이트
        2. UI 업데이트
        3. 로그 메시지 출력
        """
        # 로직 리스트 컨트롤러를 통해 저장된 로직 정보 가져오기
        saved_logics = self.logic_list_controller.get_saved_logics()
        self.logic_maker_tool_widget.update_saved_logics(saved_logics)
        self.modal_log_manager.log(
            message=f"로직 '{logic_info.get('name', '')}'이(가) 수정되었습니다",
            level="INFO",
            modal_name="로직상세"
        )

    def _on_logic_deleted(self, logic_name):
        """로직이 삭제되었을 때 호출"""
        # 로직 리스트 컨트롤러를 통해 저장된 로직 정보 가져오기
        saved_logics = self.logic_list_controller.get_saved_logics()
        self.logic_maker_tool_widget.update_saved_logics(saved_logics)
        # 로직 정보 초기화
        self.logic_detail_widget.clear_all()
        self.modal_log_manager.log(
            message=f"로직 '{logic_name}'이(가) 삭제되었습니다",
            level="INFO",
            modal_name="로직리스트"
        )

    def _on_process_selected(self, process_info):
        """프로세스가 선택되었을 때 호출"""
        self.process_manager.set_selected_process(process_info)
        self.modal_log_manager.log(
            message=f"프로세스를 선택했습니다: {process_info}",
            level="INFO",
            modal_name="프로세스"
        )
    
    def _on_process_reset(self):
        """프로세스가 초기화되었을 때 호출"""
        self.process_manager.set_selected_process(None)
        self.modal_log_manager.log(
            message="프로세스 선택이 초기화되었습니다",
            level="INFO",
            modal_name="프로세스"
        )

    def _on_add_logic(self, logic_name):
        """새로운 로직 추가 처리
        
        LogicMakerToolWidget에서 전달된 새로운 로직 정보를 처리합니다.
        
        Args:
            logic_info (dict): 로직 정보
                - name (str): 로직 이름
                - items (list): 로직 아이템 목록
                - trigger_key (dict): 트리거 키 정보
                
        프로세스:
        1. 로직 정보 유효성 검사
        2. 설정에 저장
        3. UI 업데이트
        4. 로그 메시지 출력
        """
        if logic_name in self.logic_list_controller.get_saved_logics():
            # 로직 정보에서 이름을 가져와서 아이템으로 추가
            logic_info = self.logic_list_controller.get_logic_by_name(logic_name)
            display_name = logic_info.get('name', logic_name)
            self.logic_detail_widget.add_item(display_name)
            self.modal_log_manager.log(
                message=f"로직 '{display_name}'이(가) 추가되었습니다",
                level="INFO",
                modal_name="로직상세"
            )

    def _on_wait_click_input(self, wait_click_info):
        """클릭 대기 입력 처리
        
        LogicMakerToolWidget에서 전달된 클릭 대기 정보를 처리합니다.
        
        Args:
            wait_info (dict): 클릭 대기 정보
                - x (int): 대기할 X 좌표
                - y (int): 대기할 Y 좌표
                - timeout (float): 대기 시간 제한
                
        프로세스:
        1. 대기 정보를 표시 형식으로 변환
        2. LogicDetailWidget에 추가
        """
        try:
            display_text = wait_click_info.get('display_text', '')
            self.modal_log_manager.log(
                message=f"클릭 대기 아이템이 추가되었습니다: {display_text}",
                level="INFO",
                modal_name="로직상세"
            )
            
            # 로직 상세 위젯에 클릭 대기 입력 추가
            if self.logic_detail_widget:
                self.logic_detail_widget.add_item(wait_click_info)
                
        except Exception as e:
            self.modal_log_manager.log(
                message=f"클릭 대기 입력 처리 중 오류 발생: {str(e)}",
                level="ERROR",
                modal_name="로직상세",
                print_to_terminal=True
            )

    def _on_item_added(self, item_info):
        """아이템이 추가되었을 때의 처리
        
        Args:
            item_info (dict): 추가된 아이템 정보
                type: 아이템 타입 ('key', 'mouse_input', 'delay', 'image_search', 'text', 'wait_click' 등)
                display_text: 표시될 텍스트
                기타 타입별 필요한 정보들
        """
        # 아이템 타입에 따른 처리
        item_type = item_info.get('type')
        self.modal_log_manager.log(
            message=f"아이템이 추가되었습니다: {item_info.get('display_text', str(item_info))}",
            level="INFO",
            modal_name="로직상세(_on_item_added)"
        )

        if item_type == 'key':
            # 키 입력 처리
            self.logic_detail_widget.add_item(item_info)
            self.modal_log_manager.log(
                message=f"키 입력이 추가되었습니다: {item_info['display_text']}", 
                level="INFO",
                modal_name="로직상세"
            )
        else:
            # 다른 타입의 아이템 처리
            self.logic_detail_widget.add_item(item_info)
            self.modal_log_manager.log(
                message=f"아이템이 추가되었습니다: {item_info['display_text']}",
                level="INFO", 
                modal_name="로직상세"
            )
        # 로직 메이커 도구의 아이템 목록 업데이트
        self.logic_maker_tool_widget.items.append(item_info)

    def _on_logic_selected(self, logic_name):
        """로직이 선택되었을 때 호출"""
        # 로직 리스트 컨트롤러를 통해 로직 정보 가져오기
        logic_info = self.logic_list_controller.get_logic_by_name(logic_name)
        if logic_info:
            self.logic_detail_widget.set_logic_data(logic_info)
            self.modal_log_manager.log(
                message=f"로직 '{logic_name}'이(가) 선택되었습니다",
                level="INFO",
                modal_name="로직리스트"
            )
        else:
            self.modal_log_manager.log(
                message=f"로직 '{logic_name}'을(를) 찾을 수 없습니다",
                level="ERROR",
                modal_name="로직리스트"
            )


    def show_key_info_dialog(self):
        """키 입력 다이얼로그를 생성하고 표시합니다.
        
        이 메서드가 필요한 이유:
        1. 모달 다이얼로그의 생명주기 관리
           - 모달은 임시로 사용되는 창으로, 필요할 때만 생성되고 닫히면 제거됨
           - 메모리 효율성을 위해 필요할 때만 생성하고 사용 후 정리
           
        Returns:
            EnteredKeyInfoDialog: 생성된 다이얼로그 인스턴스
            
        사용 예시:
            dialog = self.show_key_info_dialog()
            if dialog.exec() == QDialog.Accepted:
                # 키 입력 처리
                pass
        """
        # 새로운 다이얼로그 생성
        self.entered_key_info_dialog = EnteredKeyInfoDialog(self)
        
        # 다이얼로그 표시
        return self.entered_key_info_dialog
