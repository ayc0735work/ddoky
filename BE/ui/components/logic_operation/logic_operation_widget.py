from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                             QLabel, QCheckBox, QPushButton, QDialog,
                             QMessageBox, QLineEdit, QListWidgetItem, QSpacerItem,
                             QSizePolicy)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QDoubleValidator
import copy

from ...constants.styles import (FRAME_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from BE.ui.components.process_selector.process_selector_dialog import ProcessSelectorDialog
from BE.settings.settings import Settings
from BE.settings.settings_manager import SettingsManager  # SettingsManager 추가
from ..logic_maker.key_input_dialog import KeyInputDialog  # KeyInputDialog를 여기로 이동

class LogicOperationWidget(QFrame):
    """로직 동작 온오프 위젯"""
    
    process_selected = Signal(dict)  # 프로세스가 선택되었을 때
    process_reset = Signal()  # 프로세스가 초기화되었을 때
    operation_toggled = Signal(bool)  # 로직 동작이 토글되었을 때
    force_stop = Signal()  # 강제 중지 시그널 추가
    log_message = Signal(str)  # 로그 메시지 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_process = None
        self.logic_executor = None  # LogicExecutor 인스턴스를 저장할 속성 추가
        self.settings_manager = SettingsManager()  # SettingsManager 인스턴스 추가
        self.force_stop_key = self.settings_manager.get_force_stop_key()  # 강제 중지 키 로드
        self._init_ui()
        self._connect_signals()
        self.load_delay_settings()  # 초기화 시 설정 로드
        
    def _init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 타이틀
        title = QLabel("로직 동작 기본 설정")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 첫 번째 줄 레이아웃 (로직 동작, 버튼)
        first_row = QHBoxLayout()
        first_row.setContentsMargins(0, 0, 0, 0)
        first_row.setSpacing(10)  # 체크박스와 버튼 그룹 사이 간격
        
        # 로직 동작 체크박스
        self.operation_checkbox = QCheckBox("로직 동작")
        self.operation_checkbox.toggled.connect(self._on_operation_toggled)
        first_row.addWidget(self.operation_checkbox)
        
        # 버튼 그룹 레이아웃
        button_group = QHBoxLayout()
        button_group.setContentsMargins(0, 0, 0, 0)
        button_group.setSpacing(5)  # 버튼들 사이 간격
        
        # 프로세스 선택 버튼
        self.select_process_btn = QPushButton("프로세스 선택")
        self.select_process_btn.setStyleSheet(BUTTON_STYLE)
        self.select_process_btn.clicked.connect(self._on_select_process)
        button_group.addWidget(self.select_process_btn)
        
        # 프로세스 초기화 버튼
        self.reset_process_btn = QPushButton("프로세스 초기화")
        self.reset_process_btn.setStyleSheet(BUTTON_STYLE)
        self.reset_process_btn.clicked.connect(self._on_reset_process)
        button_group.addWidget(self.reset_process_btn)
        
        # 강제 중지 버튼 추가
        self.force_stop_btn = QPushButton("로직 강제 중지")
        self.force_stop_btn.setStyleSheet(BUTTON_STYLE)
        self.force_stop_btn.clicked.connect(self._on_force_stop)
        button_group.addWidget(self.force_stop_btn)

        # 강제 중지 버튼과 라벨 사이 간격을 위한 스페이서 추가
        spacer = QSpacerItem(14, 1, QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        button_group.addSpacerItem(spacer)
        
        # 로직 강제 중지 키 설정을 첫 번째 줄로 이동
        force_stop_key_layout = QHBoxLayout()
        force_stop_key_layout.setSpacing(5)
        
        force_stop_key_label = QLabel("로직 강제 중지 키")
        force_stop_key_label.setFixedWidth(100)
        force_stop_key_layout.addWidget(force_stop_key_label)
        
        self.force_stop_key_input = QLineEdit()
        self.force_stop_key_input.setFixedWidth(100)
        self.force_stop_key_input.setEnabled(False)
        self.force_stop_key_input.setText('ESC')  # 기본값으로 ESC 키 표시
        force_stop_key_layout.addWidget(self.force_stop_key_input)
        
        # 수정하기 버튼
        self.edit_force_stop_key_btn = QPushButton("수정하기")
        self.edit_force_stop_key_btn.setStyleSheet(BUTTON_STYLE)
        self.edit_force_stop_key_btn.setFixedWidth(80)
        self.edit_force_stop_key_btn.clicked.connect(self._on_edit_force_stop_key)
        force_stop_key_layout.addWidget(self.edit_force_stop_key_btn)
        
        # 초기화 버튼
        self.reset_force_stop_key_btn = QPushButton("초기화")
        self.reset_force_stop_key_btn.setStyleSheet(BUTTON_STYLE)
        self.reset_force_stop_key_btn.setFixedWidth(80)
        self.reset_force_stop_key_btn.clicked.connect(self._on_reset_force_stop_key)
        force_stop_key_layout.addWidget(self.reset_force_stop_key_btn)
        
        button_group.addLayout(force_stop_key_layout)
        
        first_row.addLayout(button_group)
        first_row.addStretch()  # 나머지 공간을 채움
        
        layout.addLayout(first_row)
        
        # 두 번째 줄 레이아웃 (선택된 프로세스)
        second_row = QHBoxLayout()
        second_row.setContentsMargins(0, 0, 0, 0)
        
        # 선택된 프로세스 라벨
        self.selected_process_label = QLabel("선택된 프로세스: 없음")
        second_row.addWidget(self.selected_process_label)
        second_row.addStretch()
        
        layout.addLayout(second_row)
        
        # 세 번째 줄 레이아웃 (활성 프로세스)
        third_row = QHBoxLayout()
        third_row.setContentsMargins(0, 0, 0, 0)
        
        # 활성 프로세스 라벨
        self.active_process_label = QLabel("활성 프로세스: 없음")
        third_row.addWidget(self.active_process_label)
        third_row.addStretch()
        
        layout.addLayout(third_row)
        
        # 기본 지연 시간 설정 레이아웃 추가
        delay_settings_layout = QHBoxLayout()
        delay_settings_layout.setContentsMargins(0, 10, 0, 0)  # 상단에 여백 추가
        delay_settings_layout.setSpacing(10)
        
        # 입력 필드들을 담을 컨테이너
        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(5)
        
        # 키 누르기 후 공통 지연시간 입력
        key_press_layout = QVBoxLayout()
        key_press_label = QLabel("키 누르기 후\n공통 지연시간")
        key_press_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_press_input = QLineEdit()
        self.key_press_input.setFixedWidth(80)
        self.key_press_input.setEnabled(False)
        self.key_press_input.setValidator(QDoubleValidator(0.0000, 9.9999, 4))
        key_press_layout.addWidget(key_press_label)
        key_press_layout.addWidget(self.key_press_input)
        inputs_layout.addLayout(key_press_layout)
        
        # 키 떼기 후 공통 지연시간 입력
        key_release_layout = QVBoxLayout()
        key_release_label = QLabel("키 떼기 후\n공통 지연시간")
        key_release_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_release_input = QLineEdit()
        self.key_release_input.setFixedWidth(80)
        self.key_release_input.setEnabled(False)
        self.key_release_input.setValidator(QDoubleValidator(0.0000, 9.9999, 4))
        key_release_layout.addWidget(key_release_label)
        key_release_layout.addWidget(self.key_release_input)
        inputs_layout.addLayout(key_release_layout)
        
        # 마우스 입력 후 공통 지연시간 입력
        mouse_input_layout = QVBoxLayout()
        mouse_input_label = QLabel("마우스 입력 전\n공통 지연시간")
        mouse_input_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mouse_input_delay = QLineEdit()
        self.mouse_input_delay.setFixedWidth(80)
        self.mouse_input_delay.setEnabled(False)
        self.mouse_input_delay.setValidator(QDoubleValidator(0.0000, 9.9999, 4))
        mouse_input_layout.addWidget(mouse_input_label)
        mouse_input_layout.addWidget(self.mouse_input_delay)
        inputs_layout.addLayout(mouse_input_layout)
        
        # 기타 동작 후 공통 지연시간 입력
        default_delay_layout = QVBoxLayout()
        default_delay_label = QLabel("기타 동작 후\n공통 지연시간")
        default_delay_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.default_delay_input = QLineEdit()
        self.default_delay_input.setFixedWidth(80)
        self.default_delay_input.setEnabled(False)
        self.default_delay_input.setValidator(QDoubleValidator(0.0000, 9.9999, 4))
        default_delay_layout.addWidget(default_delay_label)
        default_delay_layout.addWidget(self.default_delay_input)
        inputs_layout.addLayout(default_delay_layout)
        
        delay_settings_layout.addLayout(inputs_layout)
        
        # 버튼들
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(5)
        
        self.edit_delays_btn = QPushButton("수정하기")
        self.edit_delays_btn.setStyleSheet(BUTTON_STYLE)
        self.edit_delays_btn.clicked.connect(self._on_edit_delays)
        
        self.save_delays_btn = QPushButton("저장하기")
        self.save_delays_btn.setStyleSheet(BUTTON_STYLE)
        self.save_delays_btn.setEnabled(False)
        self.save_delays_btn.clicked.connect(self._on_save_delays)
        
        self.reset_delays_btn = QPushButton("초기화")
        self.reset_delays_btn.setStyleSheet(BUTTON_STYLE)
        self.reset_delays_btn.clicked.connect(self._on_reset_delays)
        
        buttons_layout.addWidget(self.edit_delays_btn)
        buttons_layout.addWidget(self.save_delays_btn)
        buttons_layout.addWidget(self.reset_delays_btn)
        
        delay_settings_layout.addLayout(buttons_layout)
        delay_settings_layout.addStretch()  # 나머지 공간을 채움
        
        layout.addLayout(delay_settings_layout)
        
        # 기본 조작 설정 영역 추가
        operation_settings_layout = QHBoxLayout()
        operation_settings_layout.setContentsMargins(0, 10, 0, 0)  # 상단에 여백 추가
        operation_settings_layout.setSpacing(10)
        
        operation_settings_layout.addStretch()  # 남은 공간을 채움
        
        layout.addLayout(operation_settings_layout)
        
        self.setLayout(layout)
        
    def _connect_signals(self):
        """시그널 연결"""
        # 기존 시그널 연결
        # 강제 중지 키 관련 시그널 연결
        self.edit_force_stop_key_btn.clicked.connect(self._on_edit_force_stop_key)
        self.reset_force_stop_key_btn.clicked.connect(self._on_reset_force_stop_key)
        
    def _get_process_info_text(self, process):
        """프로세스 정보를 텍스트로 반환"""
        if not process:
            return "선택된 프로세스 없음"
        return f"[ PID : {process['pid']} ] {process['name']} - {process['title']}"

    def _on_operation_toggled(self, checked):
        """체크박스 상태가 변경될 때 호출"""
        if checked and not self.selected_process:
            self.operation_checkbox.blockSignals(True)  # 시그널 임시 차단
            self.operation_checkbox.setChecked(False)
            self.operation_checkbox.blockSignals(False)  # 시그널 차단 해제
            self.log_message.emit("선택된 프로세스가 없습니다. 프로세스를 먼저 선택해주세요")
            return
        self.operation_toggled.emit(checked)
        
    def _on_select_process(self):
        """프로세스 선택 버튼 클릭 시 호출"""
        dialog = ProcessSelectorDialog(self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_process:
            process = dialog.selected_process
            text = f"선택된 프로세스 : {self._get_process_info_text(process)}"
            self.selected_process_label.setText(text)
            self.selected_process = process
            self.process_selected.emit(process)  # 프로세스 정보 전체를 전달
        
    def _on_reset_process(self):
        """프로세스 초기화 버튼 클릭 시 호출"""
        self.process_reset.emit()
        self.selected_process = None
        self.selected_process_label.setText("선택된 프로세스: 없음")
        self.operation_checkbox.setChecked(False)
        
    def _on_force_stop(self):
        """강제 중지 버튼 클릭 시 호출"""
        try:
            self.log_message.emit("[디버그] 강제 중지 버튼 클릭 - 시작")
            self.force_stop.emit()
            self.log_message.emit("[디버그] 강제 중지 버튼 클릭 - 완료")
        except Exception as e:
            error_msg = f"[오류] 강제 중지 버튼 클릭 중 오류 발생: {str(e)}"
            self.log_message.emit(error_msg)
        
    def update_selected_process(self, process_name):
        """선택된 프로세스 업데이트"""
        self.selected_process_label.setText(f"선택된 프로세스: {process_name}")
        
    def update_active_process(self, process_name):
        """활성 프로세스 업데이트"""
        self.active_process_label.setText(f"활성 프로세스: {process_name}")
        
    def set_logic_executor(self, executor):
        """LogicExecutor 인스턴스 설정"""
        self.logic_executor = executor

    def copy_items(self):
        """선택된 아이템들을 복사합니다."""
        selected_items = self.get_selected_items()
        if not selected_items:
            return
        
        copied_items = []
        for item in selected_items:
            # 아이템의 딥카피 생성
            copied_item = copy.deepcopy(item)
            
            # type이 'logic'인 경우 이름으로 찾아서 UUID 설정
            if copied_item.get('type') == 'logic':
                logic_name = copied_item.get('logic_name')
                
                # 최신 로직 정보 가져오기
                logics = self.settings_manager.load_logics(force=True)
                
                # 이름으로 찾기
                found = False
                for existing_id, existing_logic in logics.items():
                    if existing_logic.get('name') == logic_name:
                        logic_id = existing_id
                        found = True
                        break
                
                # 로직을 찾지 못한 경우
                if not found:
                    QMessageBox.critical(
                        self,
                        "오류",
                        f"로직 '{logic_name}'을(를) 찾을 수 없습니다.\n"
                        "해당 로직이 삭제되었거나 이름이 변경되었을 수 있습니다."
                    )
                    return
                
                # 찾은 로직 정보로 업데이트
                copied_item['logic_id'] = logic_id
                copied_item['logic_name'] = logic_name
                copied_item['display_text'] = logic_name
                if 'logic_data' in copied_item:
                    copied_item['logic_data']['logic_id'] = logic_id
                    copied_item['logic_data']['logic_name'] = logic_name
                
            copied_items.append(copied_item)
        
        # 복사된 아이템들을 클립보드에 저장
        self._clipboard = copied_items

    def paste_items(self):
        """클립보드의 아이템들을 붙여넣기"""
        if not self._clipboard:
            return
            
        try:
            # 현재 선택된 아이템의 위치 확인
            current_item = self.LogicItemList__QListWidget.currentItem()
            if current_item:
                insert_position = self.LogicItemList__QListWidget.row(current_item) + 1
            else:
                insert_position = self.LogicItemList__QListWidget.count()
            
            # 클립보드의 아이템들을 복사
            pasted_items = []
            for item in self._clipboard:
                # 아이템의 딥카피 생성
                copied_item = copy.deepcopy(item)
                
                # type이 'logic'인 경우 이름으로 찾아서 UUID 설정
                if copied_item.get('type') == 'logic':
                    logic_name = copied_item.get('logic_name')
                    
                    # 최신 로직 정보 가져오기
                    logics = self.settings_manager.load_logics(force=True)
                    
                    # 이름으로 찾기
                    found = False
                    for existing_id, existing_logic in logics.items():
                        if existing_logic.get('name') == logic_name:
                            logic_id = existing_id
                            found = True
                            break
                    
                    # 로직을 찾지 못한 경우
                    if not found:
                        QMessageBox.critical(
                            self,
                            "오류",
                            f"로직 '{logic_name}'을(를) 찾을 수 없습니다.\n"
                            "해당 로직이 삭제되었거나 이름이 변경되었을 수 있습니다."
                        )
                        return
                    
                    # 찾은 로직 정보로 업데이트
                    copied_item['logic_id'] = logic_id
                    copied_item['logic_name'] = logic_name
                    copied_item['display_text'] = logic_name
                    if 'logic_data' in copied_item:
                        copied_item['logic_data']['logic_id'] = logic_id
                        copied_item['logic_data']['logic_name'] = logic_name
                
                pasted_items.append(copied_item)
            
            # 선택된 위치 이후의 아이템들의 order 값을 조정
            next_order = 1
            # 이전 아이템들의 order 값 가져오기
            for i in range(insert_position):
                item = self.LogicItemList__QListWidget.item(i)
                if item:
                    item_data = item.data(Qt.UserRole)
                    next_order = item_data.get('order', next_order) + 1

            # 붙여넣을 아이템들의 order 값 설정
            for copied_item in pasted_items:
                copied_item['order'] = next_order
                next_order += 1
                self._add_item_at_index(copied_item, insert_position)
                insert_position += 1

            # 이후 아이템들의 order 값 업데이트
            for i in range(insert_position, self.LogicItemList__QListWidget.count()):
                item = self.LogicItemList__QListWidget.item(i)
                if item:
                    item_data = item.data(Qt.UserRole)
                    item_data['order'] = next_order
                    next_order += 1
                    item.setData(Qt.UserRole, item_data)
            
            # 변경 사항 저장
            self.save_items()
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "오류",
                f"아이템 붙여넣기 중 오류가 발생했습니다: {str(e)}"
            )

    def _add_logic_item(self, item_info):
        """로직 아이템을 리스트에 추가"""
        if not isinstance(item_info, dict):
            return
            
        # 이미 변환된 형식인 경우 (로직 타입)
        if item_info.get('type') == 'logic':
            logic_name = item_info.get('logic_name')
            
            # 최신 로직 정보 가져오기
            logics = self.settings_manager.load_logics(force=True)
            
            # 이름으로 찾기
            found = False
            for existing_id, existing_logic in logics.items():
                if existing_logic.get('name') == logic_name:
                    logic_id = existing_id
                    found = True
                    break
            
            # 로직을 찾지 못한 경우
            if not found:
                QMessageBox.critical(
                    self,
                    "오류",
                    f"로직 '{logic_name}'을(를) 찾을 수 없습니다.\n"
                    "해당 로직이 삭제되었거나 이름이 변경되었을 수 있습니다."
                )
                return
            
            # 찾은 로직 정보로 업데이트
            item_info['logic_id'] = logic_id
            item_info['logic_name'] = logic_name
            item_info['display_text'] = logic_name
            if 'logic_data' in item_info:
                item_info['logic_data']['logic_id'] = logic_id
                item_info['logic_data']['logic_name'] = logic_name
        
        # 리스트에 아이템 추가
        self._add_item_to_list(item_info)
            
    def _add_item_to_list(self, item_info):
        """아이템을 리스트에 추가"""
        if not isinstance(item_info, dict):
            return
            
        # 마우스 입력 데이터인 경우 직렬화
        if item_info.get('type') == 'mouse_input':
            serialized_data = MouseDataHandler.serialize(item_info)
            item = QListWidgetItem(item_info.get('display_text', ''))
            item.setData(Qt.UserRole, serialized_data)
        else:
            item = QListWidgetItem(item_info.get('display_text', ''))
            item.setData(Qt.UserRole, item_info)
            
        self.LogicItemList__QListWidget.addItem(item)

    def _on_edit_delays(self):
        """지연 시간 수정 버튼 클릭 시 호출"""
        self.key_press_input.setEnabled(True)
        self.key_release_input.setEnabled(True)
        self.mouse_input_delay.setEnabled(True)
        self.default_delay_input.setEnabled(True)
        self.save_delays_btn.setEnabled(True)
        self.edit_delays_btn.setEnabled(False)
    
    def _on_save_delays(self):
        """지연 시간 저장 버튼 클릭 시 호출"""
        try:
            # 입력값 가져오기
            key_press = float(self.key_press_input.text())
            key_release = float(self.key_release_input.text())
            mouse_input_delay = float(self.mouse_input_delay.text())
            default_delay = float(self.default_delay_input.text())
            
            # 로직 실행기의 딜레이 값 업데이트
            if self.logic_executor:
                self.logic_executor.KEY_DELAYS = {
                    '누르기': key_press,
                    '떼기': key_release,
                    '마우스 입력': mouse_input_delay,
                    '기본': default_delay
                }
            
            # 설정 파일에 저장
            self.settings_manager.set('key_delays', {
                'press': key_press,
                'release': key_release,
                'mouse_input': mouse_input_delay,
                'default': default_delay
            })
            
            # UI 상태 업데이트
            self.key_press_input.setEnabled(False)
            self.key_release_input.setEnabled(False)
            self.mouse_input_delay.setEnabled(False)
            self.default_delay_input.setEnabled(False)
            self.save_delays_btn.setEnabled(False)
            self.edit_delays_btn.setEnabled(True)
            
            self.log_message.emit("지연 시간 설정이 저장되었습니다.")
            
        except ValueError:
            self.log_message.emit("올바른 숫자 형식을 입력해주세요.")
    
    def load_delay_settings(self):
        """저장된 지연 시간 설정 로드"""
        delays = self.settings_manager.get('key_delays', {
            'press': 0.0245,
            'release': 0.0245,
            'mouse_input': 0.0245,
            'default': 0.0245
        })
        
        # 입력 필드에 값 설정
        self.key_press_input.setText(f"{delays['press']:.4f}")
        self.key_release_input.setText(f"{delays['release']:.4f}")
        self.mouse_input_delay.setText(f"{delays['mouse_input']:.4f}")
        self.default_delay_input.setText(f"{delays['default']:.4f}")

    def _on_reset_delays(self):
        """지연 시간 초기화 버튼 클릭 시 호출"""
        DEFAULT_DELAY = 0.0245
        
        # 입력 필드에 기본값 설정
        self.key_press_input.setText(f"{DEFAULT_DELAY:.4f}")
        self.key_release_input.setText(f"{DEFAULT_DELAY:.4f}")
        self.mouse_input_delay.setText(f"{DEFAULT_DELAY:.4f}")
        self.default_delay_input.setText(f"{DEFAULT_DELAY:.4f}")
        
        # 설정 파일에 저장
        self.settings_manager.set('key_delays', {
            'press': DEFAULT_DELAY,
            'release': DEFAULT_DELAY,
            'mouse_input': DEFAULT_DELAY,
            'default': DEFAULT_DELAY
        })
        
        # 로직 실행기의 딜레이 값 업데이트
        if self.logic_executor:
            self.logic_executor.KEY_DELAYS = {
                '누르기': DEFAULT_DELAY,
                '떼기': DEFAULT_DELAY,
                '마우스 입력': DEFAULT_DELAY,
                '기본': DEFAULT_DELAY
            }
        
        self.log_message.emit("지연 시간이 기본값으로 초기화되었습니다.")

    def _on_edit_force_stop_key(self):
        """강제 중지 키 수정 버튼 클릭 시 호출"""
        try:
            # 버튼 비활성화
            self.edit_force_stop_key_btn.setEnabled(False)
            
            # KeyInputDialog를 사용하여 키 입력 받기
            dialog = KeyInputDialog(self)
            
            # 다이얼로그를 모달로 실행하고 결과 확인
            result = dialog.exec()
            
            # 다이얼로그가 승인되었을 때만 처리
            if result == QDialog.Accepted:
                key_info = dialog.get_key_info()
                if key_info:
                    # modifiers가 KeyboardModifier 객체인 경우 정수로 변환
                    if 'modifiers' in key_info and hasattr(key_info['modifiers'], 'value'):
                        key_info['modifiers'] = int(key_info['modifiers'].value)
                    
                    self.force_stop_key = key_info
                    self.force_stop_key_input.setText(key_info['key_code'])
                    
                    # LogicExecutor에 새로운 강제 중지 키 정보 전달
                    if self.logic_executor:
                        self.logic_executor.set_force_stop_key(key_info['virtual_key'])
                    
                    # 설정 파일에 저장
                    self.settings_manager.set_force_stop_key(key_info)
                    
                    self.log_message.emit(f"로직 강제 중지 키가 '{key_info['key_code']}'(으)로 변경되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"강제 중지 키 설정 중 오류 발생: {str(e)}")
        finally:
            # 버튼 다시 활성화
            self.edit_force_stop_key_btn.setEnabled(True)
            
    def _on_reset_force_stop_key(self):
        """강제 중지 키 초기화 버튼 클릭 시 호출"""
        try:
            # ESC 키로 초기화
            self.force_stop_key = {
                "type": "key_input",
                "key_code": "ESC",
                "scan_code": 1,
                "virtual_key": 27,
                "modifiers": 0
            }
            self.force_stop_key_input.setText('ESC')
            
            # LogicExecutor에 초기화된 강제 중지 키 정보 전달
            if self.logic_executor:
                self.logic_executor.set_force_stop_key(27)
                
            # 설정 파일에 저장
            self.settings_manager.set_force_stop_key(self.force_stop_key)
                
            self.log_message.emit("로직 강제 중지 키가 'ESC'로 초기화되었습니다.")
        except Exception as e:
            self.log_message.emit(f"[오류] 강제 중지 키 초기화 중 오류 발생: {str(e)}")

    def _add_item_at_index(self, item_data, index):
        """특정 인덱스에 아이템 추가"""
        items = self.logic_data.get('items', [])
        
        # 새로운 아이템의 order 값 계산
        if index == 0:
            new_order = 1
        elif index >= len(items):
            new_order = (items[-1].get('order', 0) if items else 0) + 1
        else:
            # 삽입 위치의 이전과 다음 아이템의 order 값 사이의 중간값 계산
            prev_order = items[index - 1].get('order', 0) if index > 0 else 0
            next_order = items[index].get('order', 0)
            new_order = prev_order + (next_order - prev_order) / 2

        # 새로운 아이템에 order 값 설정
        item_data['order'] = new_order
        
        # 아이템 삽입
        items.insert(index, item_data)
        self.logic_data['items'] = items
        
        # UI 업데이트
        self._update_items_list()
        self._save_logic()
