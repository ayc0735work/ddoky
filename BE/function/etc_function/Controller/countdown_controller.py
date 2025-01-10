import threading
import time
import logging
import sys
from PySide6.QtCore import QObject, Signal, QTimer, Qt, QThread
from time import perf_counter

class CountdownWorker(QThread):
    """카운트다운 워커 스레드"""
    time_updated = Signal(float)
    finished = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._target_end_time = None
        self._is_running = False
        
    def set_target_time(self, target_time):
        self._target_end_time = target_time
        
    def stop(self):
        self._is_running = False
        
    def run(self):
        self._is_running = True
        while self._is_running and self._target_end_time:
            current_time = perf_counter()
            remaining = max(0, self._target_end_time - current_time)
            
            self.time_updated.emit(remaining)
            
            if remaining <= 0:
                break
                
            # QThread의 내장 이벤트 루프 사용
            self.msleep(1)
            
        self.finished.emit()
        self._is_running = False

class CountdownController(QObject):
    """카운트다운 컨트롤러"""
    
    countdown_updated = Signal(float)  # 카운트다운 값이 업데이트될 때 발생하는 시그널
    countdown_finished = Signal()      # 카운트다운이 완료될 때 발생하는 시그널
    
    def __init__(self):
        super().__init__()
        self._countdown_value = 10.00
        self._is_running = False
        self._start_time = None
        self._target_end_time = None
        self._last_update_time = None
        
        # 워커 스레드 초기화
        self._worker = CountdownWorker()
        self._worker.time_updated.connect(self._update_time)
        self._worker.finished.connect(self._on_worker_finished)
        
        # 타이머 초기화 (고정밀 타이머로 설정)
        self._timer = QTimer()
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._on_timeout)
        self._timer.setInterval(16)  # 약 60fps로 업데이트
        
        # 스레드 동기화를 위한 락
        self._lock = threading.Lock()
        
        # 성능 모니터링
        self._performance_stats = {
            'updates': 0,
            'delays': 0,
            'max_delay': 0
        }
        
        logging.debug("[CountdownController] 초기화 완료")
        
    def is_running(self):
        """현재 카운트다운 실행 상태 반환"""
        return self._is_running
        
    def start_countdown(self):
        """카운트다운 시작"""
        if not self._is_running:
            logging.debug("[CountdownController] 카운트다운 시작")
            with self._lock:
                self._is_running = True
                self._countdown_value = 10.00
                self._start_time = perf_counter()
                self._target_end_time = self._start_time + 10.0
                self._last_update_time = self._start_time
            
            # 워커 스레드 시작
            self._worker.set_target_time(self._target_end_time)
            self._worker.start()
            
            self._timer.start()
            self.countdown_updated.emit(self._countdown_value)
        
    def stop_countdown(self):
        """카운트다운 중지"""
        if self._is_running:
            logging.debug("[CountdownController] 카운트다운 중지")
            with self._lock:
                self._is_running = False
                self._timer.stop()
                self._worker.stop()
                self._countdown_value = 10.00
                self._start_time = None
                self._target_end_time = None
                self._last_update_time = None
            self.countdown_updated.emit(self._countdown_value)
    
    def _update_time(self, remaining_time):
        """워커 스레드로부터 시간 업데이트 수신"""
        with self._lock:
            self._countdown_value = round(remaining_time, 2)
        
    def _on_worker_finished(self):
        """워커 스레드 완료 처리"""
        logging.debug("[CountdownController] 워커 스레드 완료")
        self.stop_countdown()
        self.countdown_finished.emit()
        
    def _on_timeout(self):
        """타이머 타임아웃 처리 (UI 업데이트용)"""
        if not self._is_running:
            return
            
        current_time = perf_counter()
        
        with self._lock:
            # 타이머 지연 감지 및 기록
            if self._last_update_time:
                update_delay = current_time - self._last_update_time - (self._timer.interval() / 1000.0)
                if update_delay > 0.1:  # 100ms 이상 지연 시
                    self._performance_stats['delays'] += 1
                    self._performance_stats['max_delay'] = max(self._performance_stats['max_delay'], update_delay)
                    logging.warning(f"[CountdownController] 타이머 지연 감지: {update_delay:.3f}초")
            
            self._performance_stats['updates'] += 1
            self._last_update_time = current_time
            
            # UI 업데이트
            self.countdown_updated.emit(self._countdown_value)
