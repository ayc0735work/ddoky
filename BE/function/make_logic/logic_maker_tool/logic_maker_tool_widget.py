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
from BE.function.make_logic.repository.logic_item_manage_repository import LogicItemManageRepository

class LogicMakerToolWidget(QFrame):
    """로직 메이커 위젯"""
    # 시그널 정의
    mouse_input = Signal(dict)  # 마우스 입력이 추가되었을 때 (마우스 정보를 딕셔너리로 전달)
    delay_input = Signal(str)  # 지연시간이 추가되었을 때
    record_mode = Signal(bool)  # 기록 모드가 토글되었을 때
    add_logic = Signal(str)  # 만든 로직 추가 시그널 (로직 이름)
    wait_click_input = Signal(dict)  # 클릭 대기 입력이 추가되었을 때

    def __init__(self, parent=None):
        super().__init__(parent)
        self.repository = None  # repository는 외부에서 설정
        self._Logic_Maker_Tool_key_info_controller = None  # controller도 repository 설정 후 생성
        self.modal_log_manager = BaseLogManager.instance()
        self.init_ui()

    @property
    def repository(self):
        return self._repository
        
    @repository.setter
    def repository(self, value):
        self._repository = value
        if value is not None:
            self._Logic_Maker_Tool_key_info_controller = LogicMakerToolKeyInfoController(value)

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

    def _open_key_input_dialog(self):
        """키 입력을 요청하는 다이얼로그를 표시하고 입력된 키 정보를 처리합니다."""
        dialog = EnteredKeyInfoDialog(self)
        if dialog.exec() == QDialog.Accepted:
            entered_key_info = dialog.get_entered_key_info_result()
            if entered_key_info:
                self._Logic_Maker_Tool_key_info_controller.key_state_info_process(entered_key_info)

    def _add_mouse_input(self):
        """마우스 입력 추가"""
        dialog = MouseInputDialog(self)
        dialog.mouse_input_selected.connect(self._on_mouse_input_selected)
        dialog.exec()

    def _on_mouse_input_selected(self, mouse_info):
        """마우스 입력이 선택되었을 때"""
        processed_info = {
            'type': 'mouse_input',
            'action': mouse_info.get('action', '클릭'),
            'button': mouse_info.get('button', '왼쪽 버튼'),
            'name': mouse_info.get('name', '마우스클릭'),
            'coordinates_x': mouse_info.get('coordinates_x', 0),
            'coordinates_y': mouse_info.get('coordinates_y', 0),
            'ratios_x': mouse_info.get('ratios_x', 0),
            'ratios_y': mouse_info.get('ratios_y', 0),
            'display_text': mouse_info.get('display_text', f'마우스 입력: 마우스클릭 ({mouse_info.get("coordinates_x", 0)}, {mouse_info.get("coordinates_y", 0)})')
        }
        # Repository에 직접 저장
        self.repository.add_item(processed_info)

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
            self._on_delay_input(delay_info)

    def _on_delay_input(self, delay_info):
        """지연시간 입력 처리"""
        try:
            self.modal_log_manager.log(
                message=f"지연시간 {delay_info.get('duration', 0.0):.4f}초가 추가되었습니다",
                level="INFO",
                file_name="logic_maker_tool_widget"
            )
            # Repository를 통해 아이템 추가
            self.repository.add_item(delay_info)
        except Exception as e:
            self.modal_log_manager.log(
                message=f"지연시간 입력 처리 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_maker_tool_widget"
            )

    def _add_wait_click(self):
        """왼쪽 버튼 클릭시 다음으로 진행 추가"""
        wait_click_info = {
            'type': 'wait_click',
            'display_text': '왼쪽 버튼 클릭시 다음으로 진행',
            'button': 'left'
        }
        self._on_wait_click_input(wait_click_info)

    def _on_wait_click_input(self, wait_click_info):
        """클릭 대기 입력 처리"""
        try:
            self.modal_log_manager.log(
                message=f"{wait_click_info.get('display_text', '')} 아이템이 추가되었습니다",
                level="INFO",
                file_name="logic_maker_tool_widget"
            )
            # Repository를 통해 아이템 추가
            self.repository.add_item(wait_click_info)
        except Exception as e:
            self.modal_log_manager.log(
                message=f"클릭 대기 입력 처리 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_maker_tool_widget"
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
                image_search_info = {
                    'type': 'image_search',
                    'display_text': '이미지 서치 체크',
                    'area': area
                }
                # Repository를 통해 아이템 추가
                self.repository.add_item(image_search_info)
                self.modal_log_manager.log(
                    message=f"이미지 서치 체크 영역이 추가되었습니다: {area}",
                    level="INFO",
                    file_name="logic_maker_tool_widget"
                )

    def _add_text_input(self):
        """텍스트 입력 추가"""
        dialog = TextInputDialog(self)
        if dialog.exec() == QDialog.Accepted:
            text_info = dialog.get_text()  # 이미 딕셔너리를 반환
            if text_info:
                # Repository를 통해 아이템 추가
                self.repository.add_item(text_info)
                self.modal_log_manager.log(
                    message=f"텍스트 입력이 추가되었습니다: {text_info['text']}",
                    level="INFO",
                    file_name="logic_maker_tool_widget"
                )

    def update_saved_logics(self, logics):
        """저장된 로직 정보 업데이트"""
        self.saved_logics = logics