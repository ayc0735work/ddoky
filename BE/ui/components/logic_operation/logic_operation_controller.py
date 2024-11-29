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
        try:
            self.widget = widget
            self.widget.log_message.emit("[디버그] LogicOperationController 초기화 시작")
            super().__init__()
            self.setup_connections()
            
            # 활성 프로세스 업데이트 타이머 설정
            self.active_process_timer = QTimer()
            self.active_process_timer.timeout.connect(self._update_active_process)
            self.active_process_timer.start(100)  # 100ms 간격으로 업데이트
            self.widget.log_message.emit("[디버그] LogicOperationController 초기화 완료")
        except Exception as e:
            error_msg = f"[오류] 컨트롤러 초기화 중 오류 발생: {str(e)}"
            if hasattr(self, 'widget'):
                self.widget.log_message.emit(error_msg)
        
    def setup_connections(self):
        """시그널 연결 설정"""
        self.widget.log_message.emit("[디버그] 컨트롤러의 시그널 연결을 설정합니다")
        self.widget.operation_toggled.connect(self._handle_operation_toggle)
        self.widget.process_reset.connect(self._handle_process_reset)
        self.widget.process_selected.connect(self._handle_process_selected)
        self.widget.select_process_btn.clicked.connect(self._handle_process_selection)
        self.widget.force_stop.connect(self._handle_force_stop)  # 강제 중지 시그널 연결
        self.widget.log_message.emit("[디버그] 시그널 연결이 완료되었습니다")
        
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
        try:
            print("[디버그] 컨트롤러 강제 중지 핸들러 - 시작")
            self.widget.log_message.emit("[디버그] 컨트롤러 강제 중지 핸들러 - 시작")
            
            # logic_executor 존재 여부 자세히 로깅
            if hasattr(self.widget, 'logic_executor'):
                if self.widget.logic_executor is not None:
                    print("[디버그] logic_executor 존재함")
                    self.widget.log_message.emit("[디버그] logic_executor 존재함")
                    print(f"[디버그] logic_executor 타입: {type(self.widget.logic_executor)}")
                    self.widget.log_message.emit(f"[디버그] logic_executor 타입: {type(self.widget.logic_executor)}")
                    self.widget.logic_executor.force_stop()
                    self.widget.logic_executor.cleanup_finished.connect(self._on_force_stop_cleanup_finished)
                    print("[디버그] 모든 로직이 강제 중지되었습니다")
                    self.widget.log_message.emit("[디버그] 모든 로직이 강제 중지되었습니다")
                else:
                    print("[디버그] logic_executor가 None임")
                    self.widget.log_message.emit("[디버그] logic_executor가 None임")
            else:
                print("[디버그] widget에 logic_executor 속성이 없음")
                self.widget.log_message.emit("[디버그] widget에 logic_executor 속성이 없음")
            
            print("[디버그] 컨트롤러 강제 중지 핸들러 - 완료")
            self.widget.log_message.emit("[디버그] 컨트롤러 강제 중지 핸들러 - 완료")
        except Exception as e:
            error_msg = f"[오류] 강제 중지 처리 중 오류 발생: {str(e)}"
            print(error_msg)
            self.widget.log_message.emit(error_msg)
        
        self.widget.log_message.emit("강제 중지 처리가 완료되었습니다")
        
    def _on_force_stop_cleanup_finished(self):
        """강제 중지 정리 작업 완료 후 처리"""
        print("[디버그] 강제 중지 정리 작업 완료 - 키 감지 다시 시작")
        self.widget.log_message.emit("[디버그] 강제 중지 정리 작업 완료 - 키 감지 다시 시작")
        if hasattr(self.widget, 'logic_executor'):
            if self.widget.logic_executor is not None:
                self.widget.logic_executor.cleanup_finished.disconnect(self._on_force_stop_cleanup_finished)
                self.widget.logic_executor.start_monitoring()  # 키 감지 다시 시작
        
    def _update_active_process(self):
        """활성 프로세스 정보 업데이트"""
        process = ProcessManager.get_active_process()
        if process:
            text = f"활성 프로세스 : [ PID : {process['pid']} ] {process['name']} - {process['title']}"
            self.widget.active_process_label.setText(text)
        else:
            self.widget.active_process_label.setText("활성 프로세스 : 없음")
