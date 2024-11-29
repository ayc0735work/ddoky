from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QObject, QTimer
from .logic_operation_widget import LogicOperationWidget
from BE.process.process_manager import ProcessManager
import win32con
import win32api
import time

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
        self.widget.process_selected.connect(self._handle_process_selected)
        self.widget.select_process_btn.clicked.connect(self._handle_process_selection)
        self.widget.force_stop.connect(self._handle_force_stop)  # 강제 중지 시그널 연결
        
    def _handle_operation_toggle(self, checked):
        """로직 동작 토글 처리"""
        if checked:
            self.widget.log_message.emit("프로세스에서 로직 동작을 시작합니다")
        else:
            # LogicExecutor의 인스턴스를 사용하여 모든 로직 중지
            if self.widget.logic_executor:
                self.widget.logic_executor.stop_all_logic()
            self.widget.log_message.emit("프로세스에서 로직 동작을 종료합니다")
        
    def _handle_process_reset(self):
        """프로세스 초기화 처리"""
        self.widget.log_message.emit("선택된 프로세스를 초기화 했습니다")
        
    def _handle_process_selected(self, process_info):
        """프로세스 선택 처리"""
        self.widget.log_message.emit(f"{process_info} 프로세스를 선택했습니다")
        
    def _handle_process_selection(self):
        """프로세스 선택 처리"""
        # TODO: 실제 프로세스 선택 처리 구현
        pass
        
    def _handle_force_stop(self):
        """강제 중지 처리"""
        # 모든 로직 강제 중지
        if self.widget.logic_executor:
            self.widget.logic_executor.stop_all_logic()
            self.widget.log_message.emit("모든 로직이 강제 중지되었습니다")
        
        # # 0.5초 대기 후 ESC 키 입력
        # time.sleep(0.5)
        # win32api.keybd_event(27, 0x01, 0, 0)  # ESC press (virtual_key: 27)
        # time.sleep(0.2)  # 키 입력 딜레이
        # win32api.keybd_event(27, 0x01, win32con.KEYEVENTF_KEYUP, 0)  # ESC release
        # self.widget.log_message.emit("ESC 키 입력 완료")
        
        # # 0.5초 대기 후 왼쪽 쉬프트 키 입력
        # time.sleep(0.5)
        # win32api.keybd_event(160, 0x2A, 0, 0)  # 왼쪽 쉬프트 press (virtual_key: 160)
        # time.sleep(0.2)  # 키 입력 딜레이
        # win32api.keybd_event(160, 0x2A, win32con.KEYEVENTF_KEYUP, 0)  # 왼쪽 쉬프트 release
        # self.widget.log_message.emit("왼쪽 쉬프트 키 입력 완료")
        
        self.widget.log_message.emit("강제 중지 처리가 완료되었습니다")
        
    def _update_active_process(self):
        """활성 프로세스 정보 업데이트"""
        process = ProcessManager.get_active_process()
        if process:
            text = f"활성 프로세스 : [ PID : {process['pid']} ] {process['name']} - {process['title']}"
            self.widget.active_process_label.setText(text)
        else:
            self.widget.active_process_label.setText("활성 프로세스 : 없음")
