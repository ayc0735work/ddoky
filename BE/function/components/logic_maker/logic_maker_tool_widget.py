from PySide6.QtWidgets import (QFrame, QVBoxLayout, QPushButton,
                             QLabel, QInputDialog, QDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from ...constants.styles import (FRAME_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import LOGIC_MAKER_WIDTH, BASIC_SECTION_HEIGHT
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog
from .logic_selector_dialog import LogicSelectorDialog
from .mouse_input_dialog import MouseInputDialog
from .image_search_area_dialog import ImageSearchAreaDialog
from .text_input_dialog import TextInputDialog

class LogicMakerToolWidget(QFrame):
    """로직 메이커 위젯"""
    # 시그널 정의
    confirmed_and_added_key_info = Signal(dict)  # 키 입력이 컨펌되고 추가되었을 때 (키 정보를 딕셔너리로 전달)
    mouse_input = Signal(dict)  # 마우스 입력이 추가되었을 때 (마우스 정보를 딕셔너리로 전달)
    delay_input = Signal(str)  # 지연시간이 추가되었을 때
    record_mode = Signal(bool)  # 기록 모드가 토글되었을 때
    log_message = Signal(str)  # 로그 메시지를 전달하는 시그널
    add_logic = Signal(str)  # 만든 로직 추가 시그널 (로직 이름)
    item_added = Signal(dict)  # 아이템이 추가되었을 때
    wait_click_input = Signal(dict)  # 클릭 대기 입력이 추가되었을 때

    def __init__(self, parent=None):
        super().__init__(parent)
        self.saved_logics = {}  # 저장된 로직들을 관리하는 딕셔너리
        self.items = []  # 아이템 리스트
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
        self.key_btn.clicked.connect(self._request_key_to_input)
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
        
        현재 이 메서드는 마우스 입력 정보를 처리하는 데 사용됩니다.
        키 입력의 경우 다른 경로로 처리됩니다:
        1. _add_confirmed_input_key()에서 confirmed_and_added_key_info 시그널 발생
        2. LogicDetailWidget의 add_item()이 시그널을 받아서 처리
        3. 아이템 목록 상자에 추가
        
        마우스 입력의 경우 이 메서드를 통해 처리됩니다:
        1. _on_mouse_input()에서 이 메서드 호출
        2. items 리스트에 추가
        3. item_added 시그널 발생
        
        Args:
            item (dict): 추가할 아이템 정보
                마우스 입력 정보를 포함하는 딕셔너리
        """
        self.log_message.emit(f"[DEBUG] add_item 시작 (logic_maker_tool_widget.py) - 입력받은 데이터: {item}")
        
        if isinstance(item, dict):
            self.log_message.emit("[DEBUG] 딕셔너리 형식의 데이터 처리 시작")
            self.items.append(item)
            self.item_added.emit(item)
            self.log_message.emit(f"[DEBUG] 아이템이 성공적으로 추가되었습니다. 위치: {len(self.items)}")
        else:
            self.log_message.emit(f"[ERROR] 잘못된 형식의 데이터: {type(item)}")

    def _request_key_to_input(self):
        """입력하려는 키를 요청하는 다이얼로그를 표시
        
        프로세스:
        1. EnteredKeyInfoDialog 인스턴스를 생성하여 모달 다이얼로그로 표시
        2. 사용자가 키를 입력하면 EnteredKeyInfoWidget이 keyboard_hook_handler를 통해 키 정보를 캡처
        3. 사용자가 확인(OK)을 클릭하면:
            - EnteredKeyInfoDialog.get_entered_key_info()를 통해 formatted_key_info를 가져옴
            - 키 정보가 유효하면 _add_confirmed_input_key()를 호출하여 처리
        """
        # 1. 키 입력 다이얼로그 생성 (부모를 self로 지정하여 모달로 표시)
        dialog = EnteredKeyInfoDialog(self)
        
        # 2. 다이얼로그를 모달로 실행하고 사용자 응답 확인
        # QDialog.Accepted는 사용자가 OK 버튼을 클릭했을 때 반환됨
        # 사용자가 OK 버튼을 클릭했을 때 키 입력 정보를 가져오고 키 정보를 처리하는 코드
        if dialog.exec() == QDialog.Accepted: 
            # 3. 입력된 키 정보 가져오기
            # get_entered_key_info는 키 코드, 키 이름 등을 포함하는 딕셔너리
            get_entered_key_info = dialog.get_entered_key_info()
            
            # 4. 키 정보가 유효한 경우 처리
            # _add_confirmed_input_key()는 키 정보를 로직 아이템 목록에 추가
            if get_entered_key_info:
                self._add_confirmed_input_key(get_entered_key_info)

    def _add_confirmed_input_key(self, get_entered_key_info):
        """EnteredKeyInfoDialog에서 확인된 키 입력 정보를 처리하여 키 상태 정보를 생성하고 전달합니다.

        데이터 흐름:
        1. EnteredKeyInfoDialog에서 키 입력 정보 수신
           - get_entered_key_info: 사용자가 입력하고 확인한 키 정보
           - 키 코드, 스캔 코드, 가상 키, 위치, 수정자 키 등의 정보 포함
        
        2. 로그 메시지 생성 및 전달
           - 상세 키 정보를 포함한 로그 메시지 생성
           - log_message 시그널을 통해 로그 전달
           
        3. 키 상태 정보 생성 및 전달
           3.1 누르기(Press) 이벤트
               - key_state_info_press 생성 (원본 키 정보 복사)
               - display_text에 "--- 누르기" 추가
               - confirmed_and_added_key_info 시그널로 전달
               
           3.2 떼기(Release) 이벤트
               - key_state_info_release 생성 (원본 키 정보 복사)
               - display_text에 "--- 떼기" 추가
               - confirmed_and_added_key_info 시그널로 전달
               
        4. 시그널 수신 및 처리 (MainWindow)
           - confirmed_and_added_key_info 시그널을 통해 전달된 키 상태 정보를
           - MainWindow._on_key_input()에서 수신하여 처리
           - 최종적으로 LogicDetailWidget.add_item()으로 전달되어 목록에 추가

        Args:
            get_entered_key_info (dict): EnteredKeyInfoDialog에서 받은 키 입력 정보
        """
        # 로그 메시지 생성
        log_msg = (
            f"키 입력이 추가되었습니다 [ "
            f"키: {get_entered_key_info['key_code']}, "
            f"스캔 코드 (하드웨어 고유값): {get_entered_key_info['scan_code']}, "
            f"확장 가상 키 (운영체제 레벨의 고유 값): {get_entered_key_info['virtual_key']}, "
            f"키보드 위치: {get_entered_key_info['location']}, "
            f"수정자 키: {get_entered_key_info['modifier_text']} ]"
        )

        # 로그 메시지 전달
        self.log_message.emit(log_msg)

        # 누르기 이벤트용 키 상태 정보
        key_state_info_press = get_entered_key_info.copy()
        key_state_info_press['display_text'] = f"{get_entered_key_info['key_code']} --- 누르기"
        self.confirmed_and_added_key_info.emit(key_state_info_press)
        
        # 떼기 이벤트용 키 상태 정보
        key_state_info_release = get_entered_key_info.copy()
        key_state_info_release['display_text'] = f"{get_entered_key_info['key_code']} --- 떼기"
        self.confirmed_and_added_key_info.emit(key_state_info_release)

    def _add_mouse_input(self):
        """마우스 입력 추가"""
        dialog = MouseInputDialog(self)
        dialog.mouse_input_selected.connect(self._on_mouse_input_selected)
        dialog.log_message.connect(self.log_message.emit)
        dialog.exec()

    def _on_mouse_input_selected(self, mouse_info):
        """마우스 입력이 선택되었을 때"""
        self.log_message.emit(f"[DEBUG] 마우스 입력 정보 수신: {mouse_info}")
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
        
        self.log_message.emit(f"[DEBUG] 처리된 마우스 입력 정보: {processed_info}")
        # 아이템 추가
        self.add_item(processed_info)
        self.log_message.emit(f"마우스 입력이 추가되었습니다: {processed_info['display_text']}")

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
            self.log_message.emit(f"지연시간 {delay:.4f}초가 추가되었습니다")

    def _add_wait_click(self):
        """왼쪽 버튼 클릭시 다음으로 진행 추가"""
        wait_click_info = {
            'type': 'wait_click',
            'display_text': '왼쪽 버튼 클릭시 다음으로 진행',
            'button': 'left'
        }
        self.item_added.emit(wait_click_info)  # 아이템 목록에 추가
        self.log_message.emit("왼쪽 버튼 클릭시 다음으로 진행 아이템이 추가되었습니다")

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
                self.log_message.emit(f"이미지 서치 체크 영역이 추가되었습니다: {area}")
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
                self.log_message.emit(f"텍스트 입력이 추가되었습니다: {text_info['text']}")

    def update_saved_logics(self, logics):
        """저장된 로직 정보 업데이트"""
        self.saved_logics = logics