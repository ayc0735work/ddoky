import sys
import traceback
from PySide6.QtCore import QObject, Signal

class ErrorHandler(QObject):
    """전역 예외 처리기"""
    
    error_occurred = Signal(str)  # 에러 발생 시그널
    
    def __init__(self):
        super().__init__()
        # 기존 예외 핸들러 저장
        self.original_hook = sys.excepthook
        # 새로운 예외 핸들러 설정
        sys.excepthook = self.exception_hook
        
    def exception_hook(self, exc_type, exc_value, exc_traceback):
        """예외 발생 시 호출되는 핸들러
        
        Args:
            exc_type: 예외 타입
            exc_value: 예외 값
            exc_traceback: 예외 트레이스백
        """
        # 에러 메시지 생성
        error_msg = f"에러 발생: {exc_type.__name__}: {str(exc_value)}"
        
        # 스택 트레이스 추가
        stack_trace = ''.join(traceback.format_tb(exc_traceback))
        error_msg += f"\n\n스택 트레이스:\n{stack_trace}"
        
        # 에러 시그널 발생
        self.error_occurred.emit(error_msg)
        
        # 기존 예외 핸들러도 호출
        self.original_hook(exc_type, exc_value, exc_traceback)
