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
            window_title = win32gui.GetWindowText(hwnd)
            active_process = {
                'pid': pid,
                'title': window_title,
                'hwnd': hwnd,
                'name': window_title  # name 필드 추가
            }
            print(f"활성 프로세스: {active_process}")  # 활성 프로세스 로그
            return active_process
        except Exception as e:
            print(f"활성 프로세스 정보 가져오기 실패: {e}")
            return None

    def set_selected_process(self, process_info):
        """프로세스를 선택"""
        print(f"프로세스 선택: {process_info}")  # 프로세스 선택 로그
        self._selected_process = process_info

    def is_selected_process_active(self):
        """선택된 프로세스가 현재 활성화된 프로세스인지 확인"""
        if not self._selected_process:
            return False
        
        active_process = self.get_active_process()
        if not active_process:
            return False
            
        return active_process['pid'] == self._selected_process.get('pid')
