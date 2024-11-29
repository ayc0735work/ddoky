from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                             QLabel, QCheckBox, QPushButton, QDialog,
                             QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...constants.styles import (FRAME_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from BE.ui.components.process_selector.process_selector_dialog import ProcessSelectorDialog

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
        
    def _init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 타이틀
        title = QLabel("로직 동작 온오프")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 첫 번째 줄 레이아웃 (로직 동작, 버튼들)
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
        self.force_stop_btn = QPushButton("강제 중지")
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
            self.log_message.emit(f"프로세스에서 로직 동작을 시작합니다")
            self.process_selected.emit(process)  # 프로세스 정보 전체를 전달
        
    def _on_reset_process(self):
        """프로세스 초기화 버튼 클릭 시 호출"""
        self.process_reset.emit()
        self.selected_process = None
        self.selected_process_label.setText("선택된 프로세스: 없음")
        self.operation_checkbox.setChecked(False)
        
    def _on_force_stop(self):
        """강제 중지 버튼 클릭 시 호출"""
        self.force_stop.emit()
        
    def update_selected_process(self, process_name):
        """선택된 프로세스 업데이트"""
        self.selected_process_label.setText(f"선택된 프로세스: {process_name}")
        
    def update_active_process(self, process_name):
        """활성 프로세스 업데이트"""
        self.active_process_label.setText(f"활성 프로세스: {process_name}")
