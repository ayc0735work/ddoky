import logging
import sys
from PySide6.QtCore import QTimer
from ...components.process.process_manager import ProcessManager
from .countdown_controller import CountdownController

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class EtcFunctionController:
    """기타 기능 컨트롤러"""
    
    def __init__(self, widget):
        """
        Args:
            widget: EtcFunctionWidget 인스턴스
        """
        logging.debug("[컨트롤러] 초기화 시작")
        self.widget = widget
        self.process_manager = ProcessManager()
        self.countdown_controller = CountdownController()
        self._setup_connections()
        self.widget.set_controller(self)  # 위젯에 컨트롤러 참조 설정
        
        # 활성 프로세스 체크 타이머 설정
        self.process_check_timer = QTimer()
        self.process_check_timer.timeout.connect(self._check_process_state)
        self.process_check_timer.start(100)  # 100ms 간격으로 체크
        
        logging.debug("[컨트롤러] 초기화 완료")
        
        logging.info("EtcFunctionController 초기화 완료")
        
    def _setup_connections(self):
        """시그널/슬롯 연결 설정"""
        # 카운트다운 컨트롤러 시그널 연결
        self.countdown_controller.countdown_updated.connect(self._update_countdown_label)
        logging.debug("[컨트롤러] 시그널 연결 완료")
        # 카운트다운 값 변경 시그널 연결
        self.widget.countdown_value_changed.connect(self._handle_countdown_value_changed)
        
    def _handle_countdown_value_changed(self, value):
        """카운트다운 값 변경 처리"""
        # 여기서 필요한 추가 처리를 할 수 있습니다.
        pass
        
    def get_countdown_value(self):
        """현재 설정된 카운트다운 값을 반환"""
        return self.widget.countdown_spinbox.value()
        
    def start_hellfire_countdown(self):
        """헬파이어 카운트다운 시작"""
        logging.info("[컨트롤러] 헬파이어 카운트다운 시작 요청")
        logging.info("헬파이어 카운트다운 시작")
        self.countdown_controller.start_countdown()
        
    def stop_hellfire_countdown(self):
        """헬파이어 카운트다운 중지"""
        logging.info("[컨트롤러] 헬파이어 카운트다운 중지 요청")
        logging.info("헬파이어 카운트다운 중지")
        self.countdown_controller.stop_countdown()
        
    def _update_countdown_label(self, value):
        """카운트다운 레이블 업데이트
        
        Args:
            value (float): 현재 카운트다운 값 (초)
        """
        self.widget.update_hellfire_countdown_label(f"{value:.2f}")

    def _check_process_state(self):
        """프로세스 상태 체크 및 카운트다운 제어"""
        try:
            selected_process = self.process_manager.get_selected_process()
            active_process = self.process_manager.get_active_process()
            
            if selected_process and active_process:
                is_active = selected_process['pid'] == active_process['pid']
                current_logic_enabled = self.widget.is_logic_enabled
                current_countdown_running = self.countdown_controller._running
                
                # 프로세스 상태가 변경되었을 때만 위젯 업데이트 및 로그 출력
                if is_active != self.widget.is_process_active():
                    logging.debug(f"[컨트롤러] 프로세스 상태 변경 감지 - 선택: {selected_process['pid']}, 활성: {active_process['pid']}, 일치: {is_active}, 로직활성화: {current_logic_enabled}")
                    self.widget.update_process_state(is_active)
                    
                # 상태에 따라 카운트다운 제어
                if is_active and current_logic_enabled:
                    if not current_countdown_running:
                        logging.debug("[컨트롤러] 카운트다운 시작")
                        self.start_hellfire_countdown()
                else:
                    if current_countdown_running:
                        logging.debug("[컨트롤러] 카운트다운 중지")
                        self.stop_hellfire_countdown()
                    
        except Exception as e:
            logging.error(f"[컨트롤러] 프로세스 상태 체크 중 오류 발생: {e}")
