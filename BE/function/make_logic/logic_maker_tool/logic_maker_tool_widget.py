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
from .handlers.entered_key_info_handler import EnteredKeyInfoHandler
from BE.log.manager.base_log_manager import BaseLogManager
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog

class LogicMakerToolWidget(QFrame):
    """로직 메이커 위젯"""
    # 시그널 정의
    mouse_input = Signal(dict)  # 마우스 입력이 추가되었을 때 (마우스 정보를 딕셔너리로 전달)
    delay_input = Signal(str)  # 지연시간이 추가되었을 때
    record_mode = Signal(bool)  # 기록 모드가 토글되었을 때
    add_logic = Signal(str)  # 만든 로직 추가 시그널 (로직 이름)
    item_added = Signal(dict)  # 아이템이 추가되었을 때
    wait_click_input = Signal(dict)  # 클릭 대기 입력이 추가되었을 때

    def __init__(self, parent=None):
        super().__init__(parent)
        self.saved_logics = {}  # 저장된 로직들을 관리하는 딕셔너리
        self.items = []  # 아이템 리스트
        self.modal_log_manager = BaseLogManager.instance()
        
        # 키 입력 핸들러 초기화
        self.key_handler = EnteredKeyInfoHandler(self)
        # 키 핸들러의 시그널을 위젯의 시그널로 연결
        self.key_handler.confirmed_and_added_key_info.connect(self._on_key_state_info_added)
        
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
        return self.items

    def add_item(self, item):
        """아이템을 목록에 추가합니다.
        
        이 메서드는 다음과 같은 입력 타입을 처리합니다:
        1. 마우스 입력 정보
           - _on_mouse_input_selected()에서 호출
           - 마우스 클릭, 드래그 등의 정보 포함
           
        2. 지연시간 정보
           - _add_delay()에서 호출
           - 대기 시간 정보 포함
           
        3. 클릭 대기 정보
           - _add_wait_click()에서 호출
           - 왼쪽 버튼 클릭 대기 정보 포함
           
        4. 이미지 서치 정보
           - _add_image_search()에서 호출
           - 이미지 검색 영역 정보 포함
           
        5. 텍스트 입력 정보
           - _add_text_input()에서 호출
           - 입력할 텍스트 정보 포함
           
        6. 중첩 로직 정보
           - _add_logic()에서 호출
           - 추가할 로직의 이름 정보 포함
           
        키보드 입력의 경우 별도로 처리:
        - EnteredKeyInfoDialog에서 confirmed_and_added_key_info 시그널 발생
        - _on_key_state_info_added()에서 처리
        
        Args:
            item (dict): 추가할 아이템 정보를 포함하는 딕셔너리
                type: 아이템 타입 (mouse_input, delay, wait_click 등)
                action: 수행할 동작
                기타 타입별 필요 정보
        """
        self.modal_log_manager.log(
            message=f"아이템 추가 시작 - 입력받은 데이터: {item} <br>",
            level="DEBUG",
            modal_name="로직메이커"
        )
        
        if isinstance(item, dict):
            self.modal_log_manager.log(
                message="딕셔너리 형식의 데이터 처리 시작 <br>",
                level="DEBUG",
                modal_name="로직메이커"
            )
            self.items.append(item)
            self.item_added.emit(item)
            self.modal_log_manager.log(
                message=f"아이템이 성공적으로 추가되었습니다. 위치: {len(self.items)} <br>",
                level="DEBUG",
                modal_name="로직메이커"
            )
        else:
            self.modal_log_manager.log(
                message=f"잘못된 형식의 데이터: {type(item)} <br>",
                level="ERROR",
                modal_name="로직메이커"
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
           - key_handler.handle_confirmed_key_input()을 통해 처리
           - 키 정보는 누르기/떼기 두 가지 상태로 변환되어 처리
           
        데이터 흐름:
        1. 사용자 키 입력 → 키보드 훅 → 키 정보 구조화
        2. 확인 버튼 클릭 → 키 정보 검증 → 핸들러 전달
        3. 핸들러 처리 → 시그널 발생 → UI 업데이트
        
        Note:
            키보드 입력은 다른 입력(마우스, 지연시간 등)과 달리 
            EnteredKeyInfoHandler를 통해 별도로 처리됩니다.
            이는 키 입력의 특수성(누르기/떼기 상태, 수정자 키 등)을 
            고려한 설계입니다.
        """
        # 키 입력 다이얼로그 생성
        dialog = EnteredKeyInfoDialog(self)
        
        # 다이얼로그를 모달로 실행하고 사용자 응답 확인
        # dialog.exec()는 모달 다이얼로그를 화면에 표시하고 사용자 입력을 기다리는 메서드
        # 다이얼로그가 닫힐 때까지 코드 실행을 일시 중지하고, 닫힐 때 다음 값들 중 하나를 반환:
        # - QDialog.Accepted (1): 사용자가 OK/확인 버튼을 클릭한 경우
        # - QDialog.Rejected (0): 사용자가 Cancel/취소 버튼을 클릭하거나 다이얼로그를 닫은 경우
        # 따라서 이 조건문은 사용자가 OK 버튼으로 다이얼로그를 닫았을 때만 키 입력 처리를 진행
        if dialog.exec() == QDialog.Accepted:
            # get_entered_key_info 변수에 dialog.get_entered_key_info()의 반환값(키 정보)을 저장
            # dialog.get_entered_key_info()는 사용자가 입력한 키의 정보를 반환하는 메서드

            get_entered_key_info = dialog.get_entered_key_info()
            
            # 키 정보가 유효한 경우 핸들러에 전달하여 처리
            if get_entered_key_info:
                self.key_handler.handle_confirmed_key_input(get_entered_key_info)

    def _add_mouse_input(self):
        """마우스 입력 추가"""
        dialog = MouseInputDialog(self)
        dialog.mouse_input_selected.connect(self._on_mouse_input_selected)
        dialog.exec()

    def _on_mouse_input_selected(self, mouse_info):
        """마우스 입력이 선택되었을 때"""
        self.modal_log_manager.log(
            message=f"마우스 입력 정보 수신: {mouse_info} <br>",
            level="DEBUG",
            modal_name="로직메이커"
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
            message=f"처리된 마우스 입력 정보: {processed_info} <br>",
            level="DEBUG",
            modal_name="로직메이커"
        )
        # 아이템 추가
        self.add_item(processed_info)
        self.modal_log_manager.log(
            message=f"마우스 입력이 추가되었습니다: {processed_info['display_text']} <br>",
            level="INFO",
            modal_name="로직메이커"
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
                message=f"지연시간 {delay:.4f}초가 추가되었습니다 <br>",
                level="INFO",
                modal_name="로직메이커"
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
            message="왼쪽 버튼 클릭시 다음으로 진행 아이템이 추가되었습니다 <br>",
            level="INFO",
            modal_name="로직메이커"
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
                    message=f"이미지 서치 체크 영역이 추가되었습니다: {area} <br>",
                    level="INFO",
                    modal_name="로직메이커"
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
                    message=f"텍스트 입력이 추가되었습니다: {text_info['text']} <br>",
                    level="INFO",
                    modal_name="로직메이커"
                )

    def update_saved_logics(self, logics):
        """저장된 로직 정보 업데이트"""
        self.saved_logics = logics

    def _on_key_state_info_added(self, key_state_info):
        """키 상태 정보(누르기/떼기)가 추가되었을 때의 처리
        
        Args:
            key_state_info (dict): 키 상태 정보
                {
                    'type': 'key',                # 입력 타입
                    'action': str,                # '누르기' 또는 '떼기'
                    'key_code': str,              # 키 이름 (예: 'Space')
                    'scan_code': int,             # 하드웨어 키보드의 물리적 위치 값
                    'virtual_key': int,           # Windows API 가상 키 코드
                    'modifiers': int,             # Qt 기반 수정자 키 상태
                    'location': str,              # 키보드 위치 (예: '메인')
                    'modifier_text': str,         # 수정자 키 텍스트 (예: '없음')
                    'display_text': str,          # UI 표시용 텍스트 (예: 'Space --- 누르기')
                    'detail_display_text': str    # 상세 정보 표시용 텍스트
                }
        
        데이터 흐름:
        1. EnteredKeyInfoDialog에서 사용자가 키 입력 후 확인 버튼 클릭
        2. EnteredKeyInfoHandler.handle_confirmed_key_input()에서 키 정보를 받아 처리
           - 하나의 키 입력에 대해 누르기/떼기 두 개의 상태 정보 생성
           - confirmed_and_added_key_info 시그널로 각각 전달
        3. 본 메서드에서 key_state_info로 받아 처리
           - items 리스트에 추가
           - item_added 시그널로 다른 위젯들에게 전달
           - 로그 메시지 출력
        
        Note:
            현재는 누르기/떼기 동작이 동일하여 통합 처리 방식을 사용.
            향후 각 동작에 대해 다른 처리가 필요한 경우 아래와 같은 분리 처리 방식 고려 가능:
            ```python
            def _on_key_state_info_added(self, key_state_info):
                if key_state_info['action'] == "누르기":
                    self._handle_key_press(key_state_info)
                else:
                    self._handle_key_release(key_state_info)
            ```
        """

        self.modal_log_manager.log(
            message=f"111키 입력 정보가 추가되었습니다: {key_state_info.get('display_text', str(key_state_info))} <br>",
            level="INFO", 
            modal_name="로직메이커(_on_key_state_info_added)"
        )

        # items 리스트에 추가
        #self.items.append(key_state_info)
        # item_added 시그널 발생
        self.item_added.emit(key_state_info)
        # 로그 메시지 출력
        self.modal_log_manager.log(
            message=f"키 입력 정보가 추가되었습니다: {key_state_info.get('display_text', str(key_state_info))} <br>",
            level="INFO", 
            modal_name="로직메이커(_on_key_state_info_added)"
        )