from PySide6.QtWidgets import (QFrame, QVBoxLayout, QPushButton,
                             QLabel, QInputDialog, QDialog)

from PySide6.QtCore import Qt, Signal

from PySide6.QtGui import QFont



from ...constants.styles import (FRAME_STYLE, BUTTON_STYLE,

                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)

from ...constants.dimensions import LOGIC_MAKER_WIDTH, BASIC_SECTION_HEIGHT

from .key_input_dialog import KeyInputDialog

from .logic_selector_dialog import LogicSelectorDialog

from .mouse_input_dialog import MouseInputDialog

from .image_search_area_dialog import ImageSearchAreaDialog

from .text_input_dialog import TextInputDialog



class LogicMakerToolWidget(QFrame):

    """로직 메이커 위젯"""

    

    # 시그널 정의

    key_input = Signal(dict)  # 키 입력이 추가되었을 때 (키 정보를 딕셔너리로 전달)

    mouse_input = Signal(dict)  # 마우스 입력이 추가되었을 때 (마우스 정보를 딕셔너리로 전달)

    delay_input = Signal(str)  # 지연시간이 추가되었을 때

    record_mode = Signal(bool)  # 기록 모드가 토글되��을 때

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

        title = QLabel("로직 메이커 도구")

        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))

        layout.addWidget(title)

        

        # 버튼 레이아웃

        button_layout = QVBoxLayout()

        button_layout.setContentsMargins(0, 0, 0, 0)

        button_layout.setSpacing(5)

        

        # 키 입력 버튼

        self.key_btn = QPushButton("키 입력 추가")

        self.key_btn.setStyleSheet(BUTTON_STYLE)

        self.key_btn.clicked.connect(self._add_key_input)

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

        self.wait_click_button = QPushButton("좌클릭시 다음으로 진행")

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

        

    def _add_key_input(self):

        """키 입력 추가"""

        dialog = KeyInputDialog(self)

        if dialog.exec() == QDialog.Accepted:

            key_info = dialog.get_key_info()

            if key_info:

                self._on_key_selected(key_info)

        

    def _on_key_selected(self, key_info):

        """키가 선택되었을 때"""

        # 로그 메시지 생성

        log_msg = (

            f"키 입력이 추가되었습니다 [ "

            f"키: {key_info['key_code']}, "

            f"스캔 코드 (하드웨어 고유값): {key_info['scan_code']}, "

            f"확장 가상 키 (운영체제 레벨의 고유 값): {key_info['virtual_key']}, "

            f"키보드 위치: {self._get_key_location(key_info['scan_code'])}, "

            f"수정자 키: {self._get_modifier_text(key_info['modifiers'])} ]"

        )

        

        # 로그 메시지 전달

        self.log_message.emit(log_msg)

        

        # 누르기 이벤트용 키 정보

        press_info = key_info.copy()

        press_info['display_text'] = f"{key_info['key_code']} --- 누르기"

        self.key_input.emit(press_info)

        

        # 떼기 이벤트용 키 정보

        release_info = key_info.copy()

        release_info['display_text'] = f"{key_info['key_code']} --- 떼기"

        self.key_input.emit(release_info)

            

    def _get_key_location(self, scan_code):

        """키의 키보드 위치 정보 반환"""

        if scan_code in [42, 29, 56, 91]:  # 왼쪽 Shift, Ctrl, Alt, Win

            return "키보드 왼쪽"

        elif scan_code in [54, 285, 312, 92]:  # 오른쪽 Shift, Ctrl, Alt, Win

            return "키보드 오른쪽"

        elif 71 <= scan_code <= 83:  # 숫자패드 영역

            return "숫자패드"

        return "메인 키보드"

            

    def _get_modifier_text(self, modifiers):

        """수정자 키 텍스트 생성"""

        mod_texts = []

        

        if modifiers & Qt.ShiftModifier:

            mod_texts.append("Shift")

        if modifiers & Qt.ControlModifier:

            mod_texts.append("Ctrl")

        if modifiers & Qt.AltModifier:

            mod_texts.append("Alt")

            

        return " + ".join(mod_texts) if mod_texts else "없음"

            

    def _add_mouse_input(self):

        """마우스 입력 추가"""

        dialog = MouseInputDialog(self)

        dialog.mouse_input_selected.connect(self._on_mouse_input_selected)

        dialog.log_message.connect(self.log_message.emit)

        dialog.exec()

        

    def _on_mouse_input_selected(self, mouse_info):

        """마우스 입력이 선택되었을 때"""

        # 전체 마우스 입력 정보를 전달

        self.mouse_input.emit(mouse_info)

        self.log_message.emit(f"(logic_maker_widget--_on_mouse_input_selected)마우스 입력이 추가되었습니다: {mouse_info['display_text']}")

            

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

        self.wait_click_input.emit(wait_click_info)

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

