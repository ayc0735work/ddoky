import win32gui
import win32process
import win32con
import psutil

class ProcessManager:
    @staticmethod
    def get_processes(search_text=""):
        processes = []
        
        def enum_window_callback(hwnd, results):
            if not win32gui.IsWindowVisible(hwnd):
                return True
            
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                title = win32gui.GetWindowText(hwnd)
                
                if not title:  # 창 제목이 없는 경우 스킵
                    return True
                
                try:
                    process = psutil.Process(pid)
                    process_name = process.name()
                    
                    # 검색어가 있는 경우 필터링
                    if search_text:
                        if (search_text not in title.lower() and 
                            search_text not in process_name.lower()):
                            return True
                    
                    process_info = {
                        'pid': pid,
                        'name': process_name,
                        'title': title,
                        'hwnd': hwnd
                    }
                    results.append(process_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            except Exception:
                pass
            return True
        
        win32gui.EnumWindows(enum_window_callback, processes)
        return processes

    @staticmethod
    def get_active_process():
        """현재 활성화된 창의 프로세스 정보를 반환"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            title = win32gui.GetWindowText(hwnd)
            
            if not title:  # 창 제목이 없는 경우
                return None
            
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                
                return {
                    'pid': pid,
                    'name': process_name,
                    'title': title,
                    'hwnd': hwnd
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None
        except Exception:
            return None
