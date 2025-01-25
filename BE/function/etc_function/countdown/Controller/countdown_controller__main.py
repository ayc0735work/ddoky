"""
카운트다운 컨트롤러 모듈

이 모듈은 정밀한 카운트다운 타이머 기능을 제공합니다.
주요 기능:
1. 10초 카운트다운 실행
2. 실행 중 리셋 가능
3. 고정밀 타이머 사용
4. 스레드 안전성 보장

구조:
- CountdownWorker: 실제 카운트다운을 수행하는 워커 스레드
- CountdownController: 카운트다운 전체 로직을 관리하는 컨트롤러

작동 방식:
1. CountdownController가 카운트다운 시작 요청을 받음
2. CountdownWorker 스레드가 생성되어 실제 카운트다운 수행
3. QTimer를 통해 UI 업데이트 (60fps)
4. 스레드 간 동기화를 위해 Lock 사용
"""

import threading
from time import perf_counter
from PySide6.QtCore import QObject, QThread, Qt, QTimer, Signal
from BE.log.base_log_manager import BaseLogManager

class CountdownWorker(QThread):
    """카운트다운 워커 스레드 클래스
    
    실제 카운트다운 작업을 별도 스레드에서 수행하여 UI 블로킹을 방지합니다.
    
    시그널:
        time_updated(float): 남은 시간이 업데이트될 때마다 발생
        finished(): 카운트다운이 완료되거나 중지될 때 발생
    
    주요 기능:
        - 정밀한 시간 측정 (perf_counter 사용)
        - 스레드 안전한 상태 관리
        - 중간에 안전한 정지 가능
    """
    
    time_updated = Signal(float)  # 남은 시간 업데이트 시그널
    finished = Signal()           # 완료 시그널
    
    def __init__(self, parent=None):
        """워커 스레드 초기화
        
        Args:
            parent: 부모 QObject (기본값: None)
        
        초기화 항목:
            _target_end_time: 목표 종료 시간 (None으로 초기화)
            _is_running: 실행 상태 플래그
            _lock: 스레드 동기화를 위한 Lock
        """
        super().__init__(parent)
        self.modal_log_manager = BaseLogManager.instance()
        self._target_end_time = None
        self._is_running = False
        self._lock = threading.Lock()
        
    def set_target_time(self, target_time):
        """카운트다운 목표 시간 설정
        
        Args:
            target_time (float): 카운트다운이 끝날 목표 시간 (perf_counter 기준)
            
        스레드 안전:
            Lock을 사용하여 _target_end_time 접근 보호
        """
        with self._lock:
            self._target_end_time = target_time
            remaining_time = target_time - perf_counter()
            self.modal_log_manager.log(
                message=f"카운트다운 시작: {remaining_time:.2f}초",
                level="DEBUG",
                file_name="countdown_controller_main"
            )
        
    def stop(self):
        """워커 스레드 정지
        
        실행 중인 카운트다운을 안전하게 중지합니다.
        스레드 안전: Lock을 사용하여 _is_running 플래그 접근 보호
        """
        self.modal_log_manager.log(
            message="정지 요청",
            level="DEBUG",
            file_name="countdown_controller_main"
        )
        with self._lock:
            self._is_running = False
        
    def run(self):
        """워커 스레드 메인 실행 함수
        
        카운트다운 로직:
        1. 목표 시간 유효성 검사
        2. 1ms 간격으로 남은 시간 계산
        3. 남은 시간을 time_updated 시그널로 전송
        4. 완료 또는 중지 시 finished 시그널 발생
        
        스레드 안전:
            - 모든 공유 변수 접근에 Lock 사용
            - 상태 변경 시 항상 Lock 확보
        
        최적화:
            - perf_counter로 정밀한 시간 측정
            - 1ms sleep으로 CPU 부하 최소화
        """
        with self._lock:
            if self._target_end_time is None:
                self.modal_log_manager.log(
                    message="목표 시간이 설정되지 않음",
                    level="ERROR",
                    file_name="countdown_controller_main"
                )
                return
                
            self._is_running = True
            target_time = self._target_end_time
            self.modal_log_manager.log(
                message=f"카운트다운 시작. 목표 시간: {target_time}",
                level="DEBUG",
                file_name="countdown_controller_main"
            )
        
        while True:
            with self._lock:
                if not self._is_running:
                    self.modal_log_manager.log(
                        message="정지 신호 감지",
                        level="DEBUG",
                        file_name="countdown_controller_main"
                    )
                    break
                if self._target_end_time != target_time:
                    self.modal_log_manager.log(
                        message="목표 시간 변경 감지",
                        level="DEBUG",
                        file_name="countdown_controller_main"
                    )
                    break
            
            current_time = perf_counter()
            remaining = max(0, target_time - current_time)
            
            self.time_updated.emit(remaining)
            
            if remaining <= 0:
                self.modal_log_manager.log(
                    message="카운트다운 완료",
                    level="DEBUG",
                    file_name="countdown_controller_main"
                )
                break
            
            self.msleep(1)  # 1ms 대기 (CPU 부하 감소)
        
        self.modal_log_manager.log(
            message="스레드 종료",
            level="DEBUG",
            file_name="countdown_controller_main"
        )
        with self._lock:
            self._is_running = False
        self.finished.emit()

class CountdownController(QObject):
    """카운트다운 컨트롤러 클래스
    
    카운트다운의 전체적인 상태와 로직을 관리합니다.
    
    시그널:
        countdown_updated(float): UI에 표시할 카운트다운 값 업데이트
        countdown_finished(): 카운트다운 완료
    
    주요 기능:
        - 카운트다운 시작/정지/리셋
        - 워커 스레드 생명주기 관리
        - UI 업데이트 타이머 관리
        - 성능 모니터링
    """
    
    countdown_updated = Signal(float)  # UI 업데이트용 시그널
    countdown_finished = Signal()      # 완료 알림 시그널
    
    def __init__(self):
        """컨트롤러 초기화
        
        초기화 항목:
        1. 상태 변수:
           - _countdown_value: 현재 카운트다운 값
           - _is_running: 실행 상태
           - _start_time: 시작 시간
           - _target_end_time: 목표 종료 시간
           - _last_update_time: 마지막 업데이트 시간
        
        2. 컴포넌트:
           - 워커 스레드 (_worker)
           - UI 업데이트 타이머 (_timer)
           - 스레드 동기화 Lock (_lock)
        
        3. 성능 모니터링:
           - updates: 총 업데이트 횟수
           - delays: 지연 발생 횟수
           - max_delay: 최대 지연 시간
        """
        super().__init__()
        self.modal_log_manager = BaseLogManager.instance()
        self._countdown_value = 10.00
        self._is_running = False
        self._start_time = None
        self._target_end_time = None
        self._last_update_time = None
        
        # 워커 스레드 초기화
        self._worker = None
        self._create_worker()
        
        # UI 업데이트 타이머 초기화 (60fps)
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
        
        self.modal_log_manager.log(
            message="초기화 완료",
            level="DEBUG",
            file_name="countdown_controller_main"
        )
    
    def _create_worker(self):
        """새로운 워커 스레드 생성
        
        기존 워커 정리:
        1. stop() 호출로 안전하게 중지
        2. wait()로 완전한 종료 대기
        3. deleteLater()로 메모리 정리
        
        새 워커 설정:
        1. 새 CountdownWorker 인스턴스 생성
        2. 시그널 연결 (time_updated, finished)
        """
        if self._worker is not None:
            self._worker.stop()
            self._worker.wait()
            self._worker.deleteLater()
        
        self._worker = CountdownWorker()
        self._worker.time_updated.connect(self._update_time)
        self._worker.finished.connect(self._on_worker_finished)
        self.modal_log_manager.log(
            message="새로운 워커 생성",
            level="DEBUG",
            file_name="countdown_controller_main"
        )
    
    def is_running(self):
        """현재 카운트다운 실행 상태 반환
        
        스레드 안전:
            Lock을 사용하여 _is_running 플래그 접근 보호
        """
        with self._lock:
            return self._is_running
        
    def reset_countdown(self):
        """카운트다운 리셋 (실행 중에도 가능)
        
        동작 순서:
        1. 기존 워커 정리
        2. 상태 초기화 (10초)
        3. 새 워커 생성 및 시작
        4. UI 타이머 시작
        
        스레드 안전:
            모든 상태 변경은 Lock 내에서 수행
        """
        self.modal_log_manager.log(
            message="카운트다운 리셋 시작",
            level="DEBUG",
            file_name="countdown_controller_main"
        )
        
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
            self.modal_log_manager.log(
                message="카운트다운 리셋 완료, 새로운 카운트다운 시작",
                level="DEBUG",
                file_name="countdown_controller_main"
            )
    
    def start_countdown(self):
        """카운트다운 시작
        
        실행 중이 아닐 때만 카운트다운을 시작합니다.
        """
        if not self.is_running():
            self.reset_countdown()
        
    def stop_countdown(self):
        """카운트다운 중지
        
        실행 중일 때만 카운트다운을 중지합니다.
        """
        if self.is_running():
            self.modal_log_manager.log(
                message="카운트다운 중지",
                level="DEBUG",
                file_name="countdown_controller_main"
            )
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
        """워커 스레드로부터 시간 업데이트 수신
        
        남은 시간을 _countdown_value에 저장합니다.
        
        스레드 안전:
            Lock을 사용하여 _countdown_value 접근 보호
        """
        with self._lock:
            self._countdown_value = round(remaining_time, 2)
        
    def _on_worker_finished(self):
        """워커 스레드 완료 처리
        
        카운트다운이 완료되거나 중지된 경우에만 처리합니다.
        """
        self.modal_log_manager.log(
            message="워커 스레드 완료",
            level="DEBUG",
            file_name="countdown_controller_main"
        )
        with self._lock:
            if self._countdown_value <= 0:  # 카운트다운이 정상적으로 완료된 경우에만
                self._is_running = False
                self._timer.stop()
                self.countdown_finished.emit()
                self.modal_log_manager.log(
                    message="카운트다운 정상 완료",
                    level="DEBUG",
                    file_name="countdown_controller_main"
                )
        
    def _on_timeout(self):
        """타이머 타임아웃 처리 (UI 업데이트용)
        
        타이머가 활성화되어 있을 때만 처리합니다.
        """
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
                    self.modal_log_manager.log(
                        message=f"타이머 지연 감지: {update_delay:.3f}초",
                        level="WARNING",
                        file_name="countdown_controller_main"
                    )
            
            self._performance_stats['updates'] += 1
            self._last_update_time = current_time
            
            # UI 업데이트
            self.countdown_updated.emit(self._countdown_value)
