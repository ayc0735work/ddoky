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
from BE.log.manager.modal_log_manager import ModalLogManager

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
        self.modal_log_manager = ModalLogManager.instance()
        
        # 키 입력 핸들러 초기화
        self.key_handler = EnteredKeyInfoHandler(self)
        # 키 핸들러의 시그널을 위젯의 시그널로 연결
        self.key_handler.confirmed_and_added_key_info.connect(self._on_key_info_added)
        
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

    def _request_key_to_input(self):
        """키 입력 요청 - 핸들러로 위임"""
        self.key_handler.request_key_input(self)

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

    def _on_key_info_added(self, key_info):
        """키 입력 정보가 추가되었을 때의 처리
        
        Args:
            key_info (dict): 키 입력 정보
        """
        # items 리스트에 추가
        self.items.append(key_info)
        # item_added 시그널 발생
        self.item_added.emit(key_info)