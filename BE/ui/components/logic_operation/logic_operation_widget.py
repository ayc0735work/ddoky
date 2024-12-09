from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                             QLabel, QCheckBox, QPushButton, QDialog,
                             QMessageBox, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QDoubleValidator
import copy

from ...constants.styles import (FRAME_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from BE.ui.components.process_selector.process_selector_dialog import ProcessSelectorDialog
from BE.settings import Settings

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
        
        # 기본 지연 시간 설정 레이아웃 추가
        delay_settings_layout = QHBoxLayout()
        delay_settings_layout.setContentsMargins(0, 10, 0, 0)  # 상단에 여백 추가
        delay_settings_layout.setSpacing(10)
        
        # 입력 필드들을 담을 컨테이너
        inputs_layout = QHBoxLayout()
        inputs_layout.setSpacing(5)
        
        # 키 누르기 후 지연시간 입력
        key_press_layout = QVBoxLayout()
        key_press_label = QLabel("키 누르기 후\n지연시간")
        key_press_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_press_input = QLineEdit()
        self.key_press_input.setFixedWidth(80)
        self.key_press_input.setEnabled(False)
        self.key_press_input.setValidator(QDoubleValidator(0.0000, 9.9999, 4))
        key_press_layout.addWidget(key_press_label)
        key_press_layout.addWidget(self.key_press_input)
        inputs_layout.addLayout(key_press_layout)
        
        # 키 떼기 후 지연시간 입력
        key_release_layout = QVBoxLayout()
        key_release_label = QLabel("키 떼기 후\n지연시간")
        key_release_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.key_release_input = QLineEdit()
        self.key_release_input.setFixedWidth(80)
        self.key_release_input.setEnabled(False)
        self.key_release_input.setValidator(QDoubleValidator(0.0000, 9.9999, 4))
        key_release_layout.addWidget(key_release_label)
        key_release_layout.addWidget(self.key_release_input)
        inputs_layout.addLayout(key_release_layout)
        
        # 기타 동작 후 지연시간 입력
        default_delay_layout = QVBoxLayout()
        default_delay_label = QLabel("기타 동작 후\n지연시간")
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
        
        buttons_layout.addWidget(self.edit_delays_btn)
        buttons_layout.addWidget(self.save_delays_btn)
        
        delay_settings_layout.addLayout(buttons_layout)
        delay_settings_layout.addStretch()  # 나머지 공간을 채움
        
        layout.addLayout(delay_settings_layout)
        
        # 세 번째 줄 레이아웃 (활성 프로세스)
        third_row = QHBoxLayout()
        third_row.setContentsMargins(0, 0, 0, 0)
        
        # 활성 프로세스 라벨
        self.active_process_label = QLabel("활성 프로세스: 없음")
        third_row.addWidget(self.active_process_label)
        third_row.addStretch()
        
        layout.addLayout(third_row)
        
        self.setLayout(layout)
        
    def _connect_signals(self):
        pass
        
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
                
                # settings.json에서 로직 정보 가져오기
                logics = self.settings_manager.load_logics(force=False)
                
                # 이름으로 찾기
                found = False
                for existing_id, existing_logic in logics.items():
                    if existing_logic.get('name') == logic_name:
                        logic_id = existing_id
                        found = True
                        break
                
                # 못 찾은 경우 캐시 갱신 후 다시 시도
                if not found:
                    logics = self.settings_manager.load_logics(force=True)
                    for existing_id, existing_logic in logics.items():
                        if existing_logic.get('name') == logic_name:
                            logic_id = existing_id
                            found = True
                            break
                
                # 전히 못 찾은 경우
                if not found:
                    QMessageBox.critical(
                        self,
                        "오류",
                        f"로직 '{logic_name}'을(를) 찾을 수 없습니다.\n"
                        "해당 로직이 삭제되었거나 이름이 변경되었을 수 있습니다.\n"
                        "캐시를 갱신했지만 여전히 로직을 찾을 수 없습니다."
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

    def _add_logic_item(self, item_info):
        """로직 아이템을 리스트에 추가"""
        if not isinstance(item_info, dict):
            return
            
        # 이미 변환된 형식인 경우 (로직 타입)
        if item_info.get('type') == 'logic':
            logic_name = item_info.get('logic_name')
            
            # 1. 첫 번째 시도: settings.json에서 로직 정보 가져오기
            logics = self.settings_manager.load_logics(force=False)
            
            # 이름으로 찾기
            found = False
            for existing_id, existing_logic in logics.items():
                if existing_logic.get('name') == logic_name:
                    logic_id = existing_id
                    found = True
                    break
            
            # 2. 찾지 못한 경우 캐시를 강제로 갱신하고 다시 시도
            if not found:
                logics = self.settings_manager.load_logics(force=True)  # 캐시 강제 갱신
                for existing_id, existing_logic in logics.items():
                    if existing_logic.get('name') == logic_name:
                        logic_id = existing_id
                        found = True
                        break
            
            # 3. 여전히 찾지 못한 경우 오류 메시지 표시
            if not found:
                QMessageBox.critical(
                    self,
                    "오류",
                    f"로직 '{logic_name}'을(를) 찾을 수 없습니다.\n"
                    "해당 로직이 삭제되었거나 이름이 변경되었을 수 있습니다.\n"
                    "캐시를 갱신했지만 여전히 로직을 찾을 수 없습니다."
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

    def _on_edit_delays(self):
        """지연 시간 수정 버튼 클릭 시 호출"""
        self.key_press_input.setEnabled(True)
        self.key_release_input.setEnabled(True)
        self.default_delay_input.setEnabled(True)
        self.save_delays_btn.setEnabled(True)
        self.edit_delays_btn.setEnabled(False)
    
    def _on_save_delays(self):
        """지연 시간 저장 버튼 클릭 시 호출"""
        try:
            # 입력값 가져오기
            key_press = float(self.key_press_input.text())
            key_release = float(self.key_release_input.text())
            default_delay = float(self.default_delay_input.text())
            
            # 로직 실행기의 딜레이 값 업데이트
            if self.logic_executor:
                self.logic_executor.KEY_DELAYS = {
                    '누르기': key_press,
                    '떼기': key_release,
                    '기본': default_delay
                }
            
            # 설정 파일에 저장
            settings = Settings()
            settings.set('key_delays', {
                'press': key_press,
                'release': key_release,
                'default': default_delay
            })
            
            # UI 상태 업데이트
            self.key_press_input.setEnabled(False)
            self.key_release_input.setEnabled(False)
            self.default_delay_input.setEnabled(False)
            self.save_delays_btn.setEnabled(False)
            self.edit_delays_btn.setEnabled(True)
            
            self.log_message.emit("지연 시간 설정이 저장되었습니다.")
            
        except ValueError:
            self.log_message.emit("올바른 숫자 형식을 입력해주세요.")
    
    def load_delay_settings(self):
        """저장된 지연 시간 설정 로드"""
        settings = Settings()
        delays = settings.get('key_delays', {
            'press': 0.0205,
            'release': 0.0205,
            'default': 0.0205
        })
        
        # 입력 필드에 값 설정
        self.key_press_input.setText(f"{delays['press']:.4f}")
        self.key_release_input.setText(f"{delays['release']:.4f}")
        self.default_delay_input.setText(f"{delays['default']:.4f}")
