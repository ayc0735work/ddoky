import win32gui
import win32process
from PySide6.QtCore import QObject, Signal
import logging

class ProcessManager(QObject):
    # 시그널 정의
    process_selected = Signal(dict)  # 프로세스가 선택되었을 때 발생하는 시그널
    
    def __init__(self):
        super().__init__()
        self._selected_process = None
        self._active_process = None
        self._last_active_pid = None  # 마지막 활성 프로세스 PID 저장
        logging.debug("[프로세스 매니저] 초기화 완료")

    def get_selected_process(self):
        """선택된 프로세스 정보를 반환"""
        return self._selected_process

    def get_active_process(self):
        """현재 활성화된 프로세스 정보를 반환"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            window_title = win32gui.GetWindowText(hwnd)
            active_process = {
                'pid': pid,
                'title': window_title,
                'hwnd': hwnd,
                'name': window_title
            }
            
            # PID가 변경된 경우에만 로그 출력
            if pid != self._last_active_pid:
                logging.debug(f"[프로세스 매니저] 활성 프로세스 변경: {active_process}")
                self._last_active_pid = pid
                
            return active_process
        except Exception as e:
            logging.error(f"[프로세스 매니저] 활성 프로세스 정보 가져오기 실패: {e}")
            return None

    def set_selected_process(self, process_info):
        """프로세스를 선택"""
        logging.debug(f"[프로세스 매니저] 프로세스 선택: {process_info}")
        self._selected_process = process_info
        self.process_selected.emit(process_info)  # 시그널 발생

    def is_selected_process_active(self):
        """선택된 프로세스가 현재 활성화된 프로세스인지 확인"""
        if not self._selected_process:
            return False
        
        active_process = self.get_active_process()
        if not active_process:
            return False
            
        return active_process['pid'] == self._selected_process.get('pid')
