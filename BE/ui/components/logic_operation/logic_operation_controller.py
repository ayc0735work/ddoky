from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QObject, QTimer
from .logic_operation_widget import LogicOperationWidget
from BE.process.process_manager import ProcessManager

class LogicOperationController(QObject):
    """로직 동작 온오프 컨트롤러"""
    
    def __init__(self, widget):
        super().__init__()
        self.widget = widget
        self.setup_connections()
        
        # 활성 프로세스 업데이트 타이머 설정
        self.active_process_timer = QTimer()
        self.active_process_timer.timeout.connect(self._update_active_process)
        self.active_process_timer.start(100)  # 100ms 간격으로 업데이트
        
    def setup_connections(self):
        """시그널 연결 설정"""
        self.widget.operation_toggled.connect(self._handle_operation_toggle)
        self.widget.process_reset.connect(self._handle_process_reset)
        self.widget.select_process_btn.clicked.connect(self._handle_process_selection)
        
    def _handle_operation_toggle(self, checked):
        """로직 동작 토글 처리"""
        # TODO: 실제 로직 동작 처리 구현
        pass
        
    def _handle_process_reset(self):
        """프로세스 초기화 처리"""
        # TODO: 실제 프로세스 초기화 처리 구현
        pass
        
    def _handle_process_selection(self):
        """프로세스 선택 처리"""
        # TODO: 실제 프로세스 선택 처리 구현
        pass
        
    def _update_active_process(self):
        """활성 프로세스 정보 업데이트"""
        process = ProcessManager.get_active_process()
        if process:
            text = f"활성 프로세스 : [ PID : {process['pid']} ] {process['name']} - {process['title']}"
            self.widget.active_process_label.setText(text)
        else:
            self.widget.active_process_label.setText("활성 프로세스 : 없음")