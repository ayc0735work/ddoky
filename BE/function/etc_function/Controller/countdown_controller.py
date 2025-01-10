import threading
import time
import logging
import sys
from PySide6.QtCore import QObject, Signal, QTimer

class CountdownController(QObject):
    """카운트다운 컨트롤러"""
    
    countdown_updated = Signal(float)  # 카운트다운 값이 업데이트될 때 발생하는 시그널
    countdown_finished = Signal()      # 카운트다운이 완료될 때 발생하는 시그널
    
    def __init__(self):
        super().__init__()
        self._countdown_value = 10.00
        self._is_running = False
        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timeout)
        self._timer.setInterval(10)  # 10ms 간격으로 업데이트
        logging.debug("[CountdownController] 초기화 완료")
        
    def is_running(self):
        """현재 카운트다운 실행 상태 반환"""
        return self._is_running
        
    def start_countdown(self):
        """카운트다운 시작"""
        if not self._is_running:
            logging.debug("[CountdownController] 카운트다운 시작")
            self._is_running = True
            self._countdown_value = 10.00
            self._timer.start()
            self.countdown_updated.emit(self._countdown_value)
        
    def stop_countdown(self):
        """카운트다운 중지"""
        if self._is_running:
            logging.debug("[CountdownController] 카운트다운 중지")
            self._is_running = False
            self._timer.stop()
            self._countdown_value = 10.00
            self.countdown_updated.emit(self._countdown_value)
        
    def _on_timeout(self):
        """타이머 타임아웃 처리"""
        if self._is_running and self._countdown_value > 0:
            self._countdown_value = max(0, round(self._countdown_value - 0.01, 2))
            self.countdown_updated.emit(self._countdown_value)
            
            if self._countdown_value == 0:
                logging.debug("[CountdownController] 카운트다운 완료")
                self.stop_countdown()
                self.countdown_finished.emit()
