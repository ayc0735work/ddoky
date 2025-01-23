from PySide6.QtWidgets import (QFrame, QVBoxLayout, QPushButton,
                             QLabel, QInputDialog, QDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from BE.function.constants.styles import (FRAME_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from BE.function.constants.dimensions import LOGIC_MAKER_WIDTH, BASIC_SECTION_HEIGHT
from BE.function._common_components.modal.logic_selector_modal.logic_selector_dialog import LogicSelectorDialog
from BE.function._common_components.modal.mouse_input_modal.mouse_input_dialog import MouseInputDialog
from BE.function._common_components.modal.image_search_area_modal.image_search_area_dialog import ImageSearchAreaDialog
from BE.function._common_components.modal.text_input_modal.text_input_dialog import TextInputDialog
from .logic_maker_tool_key_info_controller import LogicMakerToolKeyInfoController
from BE.log.manager.base_log_manager import BaseLogManager
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog
from BE.function.make_logic.repository.logic_item_repository import LogicItemRepository

class LogicMakerToolWidget(QFrame):
    """로직 메이커 위젯"""
    # 시그널 정의
    mouse_input = Signal(dict)  # 마우스 입력이 추가되었을 때 (마우스 정보를 딕셔너리로 전달)
    delay_input = Signal(str)  # 지연시간이 추가되었을 때
    record_mode = Signal(bool)  # 기록 모드가 토글되었을 때
    add_logic = Signal(str)  # 만든 로직 추가 시그널 (로직 이름)
    item_added = Signal(dict)  # 아이템이 추가되었을 때
    wait_click_input = Signal(dict)  # 클릭 대기 입력이 추가되었을 때

    def __init__(self, repository: LogicItemRepository, parent=None):
        super().__init__(parent)
        self.repository = repository
        self.saved_logics = {}  # 저장된 로직들을 관리하는 딕셔너리
        self.modal_log_manager = BaseLogManager.instance()
        
        # 키 입력 컨트롤러 초기화
        self.key_info_controller = LogicMakerToolKeyInfoController(self)
        # key_info_controller의 item_added 시그널을 add_item 메서드에 연결
        self.key_info_controller.item_added.connect(self.add_item)
        
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedSize(LOGIC_MAKER_WIDTH, BASIC_SECTION_HEIGHT)

        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # 타이틀
        title = QLabel("로직 만들기 도구")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)

        # 버튼 레이아웃
        button_layout = QVBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)

        # 키 입력 버튼
        self.key_btn = QPushButton("키 입력 추가")
        self.key_btn.setStyleSheet(BUTTON_STYLE)
        self.key_btn.clicked.connect(self._open_key_input_dialog)
        button_layout.addWidget(self.key_btn)

        # 마우스 입력 버튼
        self.mouse_btn = QPushButton("마우스 입력 추가")
        self.mouse_btn.setStyleSheet(BUTTON_STYLE)
        self.mouse_btn.clicked.connect(self._add_mouse_input)
        button_layout.addWidget(self.mouse_btn)

        # 지연시간 버튼
        self.delay_btn = QPushButton("지연시간 추가")
        self.delay_btn.setStyleSheet(BUTTON_STYLE)
        self.delay_btn.clicked.connect(self._add_delay)
        button_layout.addWidget(self.delay_btn)

        # 클릭 대기 버튼
        self.wait_click_button = QPushButton("왼쪽클릭시 다음으로 진행")
        self.wait_click_button.setStyleSheet(BUTTON_STYLE)
        self.wait_click_button.clicked.connect(self._add_wait_click)
        button_layout.addWidget(self.wait_click_button)

        # 이미지 서치 체크 버튼
        self.image_search_btn = QPushButton("이미지 서치 체크")
        self.image_search_btn.setStyleSheet(BUTTON_STYLE)
        self.image_search_btn.clicked.connect(self._add_image_search)
        button_layout.addWidget(self.image_search_btn)

        # 텍스트 입력 버튼
        self.text_input_btn = QPushButton("텍스트 입력")
        self.text_input_btn.setStyleSheet(BUTTON_STYLE)
        self.text_input_btn.clicked.connect(self._add_text_input)
        button_layout.addWidget(self.text_input_btn)

        # 기록 모드 버튼
        self.record_btn = QPushButton("기록 모드")
        self.record_btn.setStyleSheet(BUTTON_STYLE)
        self.record_btn.setCheckable(True)
        self.record_btn.clicked.connect(self._toggle_record_mode)
        button_layout.addWidget(self.record_btn)

        # 만든 로직 추가 버튼
        self.add_logic_btn = QPushButton("만든 로직 추가")
        self.add_logic_btn.setStyleSheet(BUTTON_STYLE)
        self.add_logic_btn.clicked.connect(self._add_logic)
        button_layout.addWidget(self.add_logic_btn)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_next_order(self):
        """다음 순서 번호를 반환합니다."""
        items = self.get_items()
        if not items:
            return 1
        return max(item.get('order', 0) for item in items) + 1

    def get_items(self):
        """아이템 목록을 반환합니다."""
        return self.repository.get_items()

    def add_item(self, item_info):
        """아이템을 목록에 추가합니다."""
        self.modal_log_manager.log(
            message=f"아이템 추가 시작 - 입력받은 데이터: {item_info}",
            level="DEBUG",
            modal_name="logic_maker_tool_widget"
        )
        
        if isinstance(item_info, dict):
            self.modal_log_manager.log(
                message="딕셔너리 형식의 데이터 처리 시작",
                level="DEBUG",
                modal_name="logic_maker_tool_widget"
            )
            # order 값이 없으면 설정
            if 'order' not in item_info:
                item_info['order'] = self.get_next_order()
            
            self.repository.add_item(item_info)  # repository를 통해 아이템 추가
            
            self.modal_log_manager.log(
                message=f"아이템이 성공적으로 추가되었습니다",
                level="DEBUG",
                modal_name="logic_maker_tool_widget"
            )
        else:
            self.modal_log_manager.log(
                message=f"잘못된 형식의 데이터: {type(item_info)}",
                level="ERROR",
                modal_name="logic_maker_tool_widget"
            )

    def _open_key_input_dialog(self):
        """키 입력을 요청하는 다이얼로그를 표시하고 입력된 키 정보를 처리합니다.
        
        이 메서드는 다음과 같은 처리를 수행합니다:
        1. 키 입력 다이얼로그 표시
           - EnteredKeyInfoDialog 인스턴스 생성
           - 모달 형태로 다이얼로그 표시
           - 사용자의 키 입력 대기
           
        2. 키 입력 감지 및 캡처
           - EnteredKeyInfoWidget이 keyboard_hook_handler를 통해 키 정보 캡처
           - 캡처된 정보는 formatted_key_info 형태로 구조화
           - NumLock 상태 등 특수 상황 처리
           
        3. 키 정보 처리 및 전달
           - 사용자가 확인(OK) 버튼 클릭 시 처리 시작
           - EnteredKeyInfoDialog.get_entered_key_info()로 키 정보 획득
           - key_info_controller.handle_confirmed_key_input()을 통해 처리
           - 키 정보는 누르기/떼기 두 가지 상태로 변환되어 처리
        """
        # 키 입력 다이얼로그 생성
        dialog = EnteredKeyInfoDialog(self)
        
        if dialog.exec() == QDialog.Accepted:
            get_entered_key_info = dialog.get_entered_key_info()
            if get_entered_key_info:
                self.key_info_controller.handle_confirmed_key_input(get_entered_key_info)

    def _add_mouse_input(self):
        """마우스 입력 추가"""
        dialog = MouseInputDialog(self)
        dialog.mouse_input_selected.connect(self._on_mouse_input_selected)
        dialog.exec()

    def _on_mouse_input_selected(self, mouse_info):
        """마우스 입력이 선택되었을 때"""
        self.modal_log_manager.log(
            message=f"마우스 입력 정보 수신: {mouse_info}",
            level="DEBUG",
            modal_name="logic_maker_tool_widget"
        )
        
        # 마우스 입력 정보 처리
        processed_info = {
            'type': 'mouse_input',
            'action': mouse_info.get('action', '클릭'),
            'button': mouse_info.get('button', '왼쪽 버튼'),
            'name': mouse_info.get('name', '마우스클릭'),
            'coordinates_x': mouse_info.get('coordinates_x', 0),
            'coordinates_y': mouse_info.get('coordinates_y', 0),
            'ratios_x': mouse_info.get('ratios_x', 0),
            'ratios_y': mouse_info.get('ratios_y', 0),
            'order': self.get_next_order(),
            'display_text': mouse_info.get('display_text', f'마우스 입력: 마우스클릭 ({mouse_info.get("coordinates_x", 0)}, {mouse_info.get("coordinates_y", 0)})')
        }
        
        self.modal_log_manager.log(
            message=f"처리된 마우스 입력 정보: {processed_info}",
            level="DEBUG",
            modal_name="logic_maker_tool_widget"
        )
        # 아이템 추가
        self.add_item(processed_info)
        self.modal_log_manager.log(
            message=f"마우스 입력이 추가되었습니다: {processed_info['display_text']}",
            level="INFO",
            modal_name="logic_maker_tool_widget"
        )

    def _add_delay(self):
        """지연시간 추가"""
        # QInputDialog 커스터마이징
        dialog = QInputDialog(self)
        dialog.setWindowTitle("지연시간")
        dialog.setLabelText("지연시간(초):")
        dialog.setDoubleDecimals(4)  # 소수점 4자리까지 표시 (0.0001초 단위)
        dialog.setDoubleValue(0.01)  # 기본값 0.01초
        dialog.setDoubleRange(0.0001, 10000.0)  # 0.0001초 ~ 10000초
        dialog.setDoubleStep(0.0001)  # 증가/감소 단위

        # 버튼 텍스트 변경
        dialog.setOkButtonText("지연시간 저장")
        dialog.setCancelButtonText("지연시간 입력 취소")

        if dialog.exec():
            delay = dialog.doubleValue()
            delay_text = f"지연시간 : {delay:.4f}초"
            delay_info = {
                'type': 'delay',
                'display_text': delay_text,
                'duration': delay
            }
            self.item_added.emit(delay_info)  # item_added 시그널로 전체 정보 전달
            self.modal_log_manager.log(
                message=f"지연시간 {delay:.4f}초가 추가되었습니다",
                level="INFO",
                modal_name="logic_maker_tool_widget"
            )

    def _add_wait_click(self):
        """왼쪽 버튼 클릭시 다음으로 진행 추가"""
        wait_click_info = {
            'type': 'wait_click',
            'display_text': '왼쪽 버튼 클릭시 다음으로 진행',
            'button': 'left'
        }
        self.item_added.emit(wait_click_info)  # 아이템 목록에 추가
        self.modal_log_manager.log(
            message="왼쪽 버튼 클릭시 다음으로 진행 아이템이 추가되었습니다",
            level="INFO",
            modal_name="logic_maker_tool_widget"
        )

    def _toggle_record_mode(self, checked):
        """기록 모드 토글"""
        self.record_mode.emit(checked)

    def _add_logic(self):
        """만든 로직 추가"""
        dialog = LogicSelectorDialog(self.saved_logics, self)
        dialog.logic_selected.connect(lambda name: self.add_logic.emit(name))
        dialog.exec()

    def _add_image_search(self):
        """이미지 서치 체크 추가"""
        dialog = ImageSearchAreaDialog(self)
        if dialog.exec() == QDialog.Accepted:
            area = dialog.captured_rect
            if area:
                self.modal_log_manager.log(
                    message=f"이미지 서치 체크 영역이 추가되었습니다: {area}",
                    level="INFO",
                    modal_name="logic_maker_tool_widget"
                )
                self.item_added.emit({
                    'type': 'image_search',
                    'display_text': '이미지 서치 체크',
                    'area': area
                })

    def _add_text_input(self):
        """텍스트 입력 추가"""
        dialog = TextInputDialog(self)
        if dialog.exec() == QDialog.Accepted:
            text_info = dialog.get_text()  # 이미 딕셔너리를 반환
            if text_info:
                self.item_added.emit(text_info)  # 직접 전달
                self.modal_log_manager.log(
                    message=f"텍스트 입력이 추가되었습니다: {text_info['text']}",
                    level="INFO",
                    modal_name="logic_maker_tool_widget"
                )

    def update_saved_logics(self, logics):
        """저장된 로직 정보 업데이트"""
        self.saved_logics = logics