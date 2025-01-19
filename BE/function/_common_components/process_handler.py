import win32gui
import win32process
import psutil
from PySide6.QtCore import QObject, Signal
import logging

class ProcessManager(QObject):
    """윈도우 프로세스 검색 및 관리 클래스
    
    윈도우 프로세스를 검색하고 선택된 프로세스를 관리하는 클래스입니다.
    프로세스 검색, 활성 프로세스 확인, 프로세스 선택 등의 기능을 제공합니다.
    """
    
    # 시그널 정의
    process_selected = Signal(dict)  # 프로세스가 선택되었을 때 발생하는 시그널
    
    def __init__(self):
        """ProcessManager 초기화"""
        super().__init__()
        self._selected_process = None
        logging.debug("[프로세스 매니저] 초기화 완료")
    
    @staticmethod
    def get_processes(search_text=""):
        """실행 중인 윈도우 프로세스 목록을 검색합니다.
        
        Args:
            search_text (str): 검색할 텍스트 (프로세스 이름이나 창 제목에 포함된 텍스트)
            
        Returns:
            list: 프로세스 정보 딕셔너리의 리스트
                 각 딕셔너리는 'pid', 'name', 'title', 'hwnd' 키를 포함
        """
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
                except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                    logging.error(f"[프로세스 매니저] 프로세스 정보 접근 실패 (PID: {pid}): {e}")
                    pass
            except Exception as e:
                logging.error(f"[프로세스 매니저] 윈도우 정보 가져오기 실패: {e}")
                pass
            return True
        
        try:
            win32gui.EnumWindows(enum_window_callback, processes)
        except Exception as e:
            logging.error(f"[프로세스 매니저] 프로세스 목록 검색 실패: {e}")
        return processes

    @staticmethod
    def get_active_process():
        """현재 활성화된 창의 프로세스 정보를 반환합니다.
        
        Returns:
            dict: 프로세스 정보 딕셔너리 ('pid', 'name', 'title', 'hwnd' 키 포함)
                 실패 시 None 반환
        """
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None

            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            window_title = win32gui.GetWindowText(hwnd)
            
            if not window_title:  # 창 제목이 없는 경우
                return None
            
            active_process = {
                'pid': pid,
                'title': window_title,
                'hwnd': hwnd,
                'name': window_title
            }
            
            return active_process
        except Exception as e:
            logging.error(f"[프로세스 매니저] 활성 프로세스 정보 가져오기 실패: {e}")
            return None
    
    def set_selected_process(self, process_info):
        """프로세스를 선택 상태로 설정합니다.
        
        Args:
            process_info (dict): 선택된 프로세스 정보
        """
        logging.debug(f"[프로세스 매니저] 프로세스 선택: {process_info}")
        self._selected_process = process_info
        self.process_selected.emit(process_info)
    
    def get_selected_process(self):
        """현재 선택된 프로세스 정보를 반환합니다.
        
        Returns:
            dict: 선택된 프로세스 정보. 없으면 None
        """
        return self._selected_process
    
    def is_selected_process_active(self):
        """선택된 프로세스가 현재 활성화된 프로세스인지 확인합니다.
        
        Returns:
            bool: 선택된 프로세스가 현재 활성화되어 있으면 True, 아니면 False
        """
        if not self._selected_process:
            return False
        
        active_process = ProcessManager.get_active_process()  
        if not active_process:
            return False
            
        return active_process['pid'] == self._selected_process.get('pid')
