from PySide6.QtCore import QObject, Signal
from typing import List, Callable
import logging
from datetime import datetime

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
        self.handlers: List[Callable] = []
        self.log_buffer = []
        self.buffer_size = 1000  # 버퍼 최대 크기
        
    def add_handler(self, handler: Callable[[str], None]):
        """로그 핸들러를 추가합니다.
        
        Args:
            handler: 로그 메시지를 처리할 콜백 함수
        """
        if handler not in self.handlers:
            self.handlers.append(handler)
            
    def remove_handler(self, handler: Callable[[str], None]):
        """로그 핸들러를 제거합니다.
        
        Args:
            handler: 제거할 핸들러
        """
        if handler in self.handlers:
            self.handlers.remove(handler)
            
    def log(self, message: str, level: str = "INFO", modal_name: str = None):
        """로그 메시지를 처리합니다.
        
        Args:
            message: 로그 메시지
            level: 로그 레벨 ("INFO", "WARNING", "ERROR" 등)
            modal_name: 로그를 발생시킨 모달의 이름
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] "
        if modal_name:
            formatted_message += f"[{modal_name}] "
        formatted_message += message
        
        # 버퍼에 추가
        self.log_buffer.append(formatted_message)
        if len(self.log_buffer) > self.buffer_size:
            self.log_buffer.pop(0)  # 가장 오래된 로그 제거
            
        # 핸들러들에게 전달
        for handler in self.handlers:
            try:
                handler(formatted_message)
            except Exception as e:
                logging.error(f"로그 핸들러 실행 중 오류 발생: {str(e)}")
                
        # 시그널 발생
        self.log_message.emit(formatted_message)
        
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