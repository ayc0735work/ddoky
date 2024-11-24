import win32gui
import win32process

class ProcessManager:
    def __init__(self):
        self._selected_process = None
        self._active_process = None

    def get_selected_process(self):
        """선택된 프로세스 정보를 반환"""
        return self._selected_process

    def get_active_process(self):
        """현재 활성화된 프로세스 정보를 반환"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            return pid
        except Exception:
            return None

    def set_selected_process(self, process_info):
        """프로세스를 선택"""
        self._selected_process = process_info

    def is_selected_process_active(self):
        """선택된 프로세스가 현재 활성화된 프로세스인지 확인"""
        if not self._selected_process:
            return False
        
        active_pid = self.get_active_process()
        return active_pid and active_pid == self._selected_process.get('pid')
