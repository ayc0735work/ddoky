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
        self._lock = threading.Lock()
        
    def set_target_time(self, target_time):
        with self._lock:
            self._target_end_time = target_time
            logging.debug(f"[CountdownWorker] 목표 시간 설정: {target_time}")
        
    def stop(self):
        logging.debug("[CountdownWorker] 정지 요청")
        with self._lock:
            self._is_running = False
        
    def run(self):
        with self._lock:
            if self._target_end_time is None:
                logging.error("[CountdownWorker] 목표 시간이 설정되지 않음")
                return
                
            self._is_running = True
            target_time = self._target_end_time
            logging.debug(f"[CountdownWorker] 카운트다운 시작. 목표 시간: {target_time}")
        
        while True:
            with self._lock:
                if not self._is_running:
                    logging.debug("[CountdownWorker] 정지 신호 감지")
                    break
                if self._target_end_time != target_time:
                    logging.debug("[CountdownWorker] 목표 시간 변경 감지")
                    break
            
            current_time = perf_counter()
            remaining = max(0, target_time - current_time)
            
            self.time_updated.emit(remaining)
            
            if remaining <= 0:
                logging.debug("[CountdownWorker] 카운트다운 완료")
                break
            
            self.msleep(1)
        
        logging.debug("[CountdownWorker] 스레드 종료")
        with self._lock:
            self._is_running = False
        self.finished.emit()

class CountdownController(QObject):
    """카운트다운 컨트롤러"""
    
    countdown_updated = Signal(float)
    countdown_finished = Signal()
    
    def __init__(self):
        super().__init__()
        self._countdown_value = 10.00
        self._is_running = False
        self._start_time = None
        self._target_end_time = None
        self._last_update_time = None
        
        # 워커 스레드 초기화
        self._worker = None
        self._create_worker()
        
        # 타이머 초기화
        self._timer = QTimer()
        self._timer.setTimerType(Qt.TimerType.PreciseTimer)
        self._timer.timeout.connect(self._on_timeout)
        self._timer.setInterval(16)
        
        self._lock = threading.Lock()
        self._performance_stats = {
            'updates': 0,
            'delays': 0,
            'max_delay': 0
        }
        
        logging.debug("[CountdownController] 초기화 완료")
    
    def _create_worker(self):
        """새로운 워커 스레드 생성"""
        if self._worker is not None:
            self._worker.stop()
            self._worker.wait()
            self._worker.deleteLater()
        
        self._worker = CountdownWorker()
        self._worker.time_updated.connect(self._update_time)
        self._worker.finished.connect(self._on_worker_finished)
        logging.debug("[CountdownController] 새로운 워커 생성")
    
    def is_running(self):
        """현재 카운트다운 실행 상태 반환"""
        with self._lock:
            return self._is_running
        
    def reset_countdown(self):
        """카운트다운 리셋 (진행 중에도 가능)"""
        logging.debug("[CountdownController] 카운트다운 리셋 시작")
        
        # 워커 스레드 중지 및 대기
        if self._worker is not None:
            self._worker.stop()
            self._worker.wait()
        
        with self._lock:
            current_time = perf_counter()
            self._countdown_value = 10.00
            self._start_time = current_time
            self._target_end_time = current_time + 10.0
            self._last_update_time = current_time
            self._is_running = True
            
            # 새로운 워커 생성 및 시작
            self._create_worker()
            self._worker.set_target_time(self._target_end_time)
            self._worker.start()
            
            # 타이머 시작
            if not self._timer.isActive():
                self._timer.start()
            
            self.countdown_updated.emit(self._countdown_value)
            logging.debug("[CountdownController] 카운트다운 리셋 완료, 새로운 카운트다운 시작")
    
    def start_countdown(self):
        """카운트다운 시작"""
        if not self.is_running():
            self.reset_countdown()
        
    def stop_countdown(self):
        """카운트다운 중지"""
        if self.is_running():
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
        with self._lock:
            if self._countdown_value <= 0:  # 카운트다운이 정상적으로 완료된 경우에만
                self._is_running = False
                self._timer.stop()
                self.countdown_finished.emit()
                logging.debug("[CountdownController] 카운트다운 정상 완료")
        
    def _on_timeout(self):
        """타이머 타임아웃 처리 (UI 업데이트용)"""
        if not self.is_running():
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
