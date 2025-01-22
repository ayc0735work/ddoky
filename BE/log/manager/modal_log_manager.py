from PySide6.QtCore import QObject, Signal
from typing import List, Callable, Optional
import logging
from datetime import datetime
import time

class ModalLogManager(QObject):
    """모달 다이얼로그의 로그를 중앙에서 관리하는 매니저
    
    이 클래스는 싱글톤 패턴을 사용하여 모든 모달 다이얼로그의 로그를 
    중앙에서 수집하고 관리합니다.
    """
    
    _instance = None
    log_message = Signal(str)  # 로그 메시지 시그널
    
    @classmethod
    def instance(cls):
        """싱글톤 인스턴스를 반환합니다."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        """초기화
        
        Note:
            직접 인스턴스화하지 말고 instance() 클래스 메서드를 사용하세요.
        """
        if ModalLogManager._instance is not None:
            raise RuntimeError("ModalLogManager는 싱글톤입니다. instance()를 사용하세요.")
            
        super().__init__()
        self._handlers = []
        self._timers = {}  # 각 모달별 타이머 저장
        self.log_buffer = []
        self.buffer_size = 1000  # 버퍼 최대 크기
        
    def add_handler(self, handler: Callable[[str], None]):
        """로그 핸들러를 추가합니다.
        
        Args:
            handler: 로그 메시지를 처리할 콜백 함수
        """
        if handler not in self._handlers:
            self._handlers.append(handler)
            
    def remove_handler(self, handler: Callable[[str], None]):
        """로그 핸들러를 제거합니다.
        
        Args:
            handler: 제거할 핸들러
        """
        if handler in self._handlers:
            self._handlers.remove(handler)
            
    def start_timer(self, modal_name: str):
        """특정 모달의 타이머 시작
        
        Args:
            modal_name: 모달 이름
        """
        self._timers[modal_name] = time.time()
        
    def reset_timer(self, modal_name: str):
        """특정 모달의 타이머 리셋
        
        Args:
            modal_name: 모달 이름
        """
        if modal_name in self._timers:
            self._timers[modal_name] = time.time()
            
    def stop_timer(self, modal_name: str):
        """특정 모달의 타이머 중지
        
        Args:
            modal_name: 모달 이름
        """
        if modal_name in self._timers:
            del self._timers[modal_name]
            
    def get_elapsed_time(self, modal_name: str) -> Optional[float]:
        """특정 모달의 경과 시간 반환
        
        Args:
            modal_name: 모달 이름
            
        Returns:
            float or None: 경과 시간(초), 타이머가 없으면 None
        """
        if modal_name in self._timers:
            return time.time() - self._timers[modal_name]
        return None
        
    def log(self, message: str, level: str = "INFO", modal_name: str = "", include_time: bool = False, print_to_terminal: bool = False):
        """로그 메시지를 기록합니다.

        Args:
            message (str): 로그 메시지
            level (str, optional): 로그 레벨. Defaults to "INFO".
            modal_name (str, optional): 모달 이름. Defaults to "".
            include_time (bool, optional): 경과 시간 포함 여부. Defaults to False.
            print_to_terminal (bool, optional): 터미널 출력 여부. Defaults to False.
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 기본 로그 형식 구성
        log_parts = [f"[{now}]"]
        
        # 경과 시간이 필요한 경우 추가
        if include_time and modal_name in self._timers:
            elapsed = time.time() - self._timers[modal_name]
            log_parts.append(f"[{elapsed:.4f}초]")
        
        # 레벨과 모달 이름 추가
        log_parts.extend([f"[{level}]", f"[{modal_name}]"])
        
        # 최종 로그 메시지 구성
        final_message = " ".join(log_parts + [message])
        
        # 터미널 출력이 요청된 경우
        if print_to_terminal:
            print(final_message)
        
        # 핸들러들에게 로그 전달
        for handler in self._handlers:
            handler(final_message)
        
        # 버퍼에 추가
        self.log_buffer.append(final_message)
        if len(self.log_buffer) > self.buffer_size:
            self.log_buffer.pop(0)  # 가장 오래된 로그 제거
            
        # 시그널 발생
        self.log_message.emit(final_message)
        
    def clear_buffer(self):
        """로그 버퍼를 비웁니다."""
        self.log_buffer.clear()
        
    def get_logs(self, count: int = None) -> List[str]:
        """저장된 로그를 반환합니다.
        
        Args:
            count: 가져올 로그의 수. None이면 전체 로그 반환
            
        Returns:
            List[str]: 로그 메시지 리스트
        """
        if count is None:
            return self.log_buffer[:]
        return self.log_buffer[-count:] 