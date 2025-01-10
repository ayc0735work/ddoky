import threading
import time
import logging
import sys
from PySide6.QtCore import QObject, Signal

class CountdownController(QObject):
    countdown_updated = Signal(float)  # 카운트다운 값을 전달하는 시그널
    
    def __init__(self):
        super().__init__()
        self._running = False
        self._thread = None
        self._lock = threading.Lock()
        
    def start_countdown(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._thread = threading.Thread(target=self._countdown_loop, daemon=True)
            self._thread.start()
    
    def stop_countdown(self):
        with self._lock:
            if not self._running:
                return
            self._running = False
            if self._thread and self._thread.is_alive():
                self._thread.join()
    
    def _countdown_loop(self):
        try:
            while self._running:
                for current in range(1000, -1, -1):  # 10.00초에서 0.00초까지
                    if not self._running:
                        break
                    current_value = current / 100
                    self.countdown_updated.emit(current_value)
                    time.sleep(0.01)  # 0.01초 간격으로 업데이트
        except Exception as e:
            logging.error(f"[카운트다운] 루프 실행 중 오류 발생: {e}")
            self._running = False
