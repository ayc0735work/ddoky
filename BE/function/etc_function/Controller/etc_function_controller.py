import logging
import sys
from PySide6.QtCore import QTimer, QObject
from ...components.process.process_manager import ProcessManager
from .countdown_controller import CountdownController
import time

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class EtcFunctionController(QObject):
    """기타 기능 컨트롤러"""
    
    def __init__(self, widget):
        super().__init__()
        logging.debug("[컨트롤러] 초기화 시작")
        self.widget = widget
        self.process_manager = ProcessManager()
        self.countdown_controller = CountdownController()
        
        # 키 상태 관리
        self._key_state = {
            'group_a_pressed': False,  # A그룹 키 눌림 상태
            'group_b_pressed': False,  # B그룹 키 눌림 상태
            'last_key_info': None,     # 마지막 키 정보
            'sequence_valid': False,    # 시퀀스 유효성
            'sequence_start_time': None # 시퀀스 시작 시간
        }
        
        # 시퀀스 타임아웃 타이머
        self._sequence_timer = QTimer()
        self._sequence_timer.setInterval(10000)  # 10초
        self._sequence_timer.timeout.connect(self._on_sequence_timeout)
        self._sequence_timer.setSingleShot(True)
        
        # 활성 프로세스 체크 타이머 설정
        self.process_check_timer = QTimer()
        self.process_check_timer.timeout.connect(self._check_process_state)
        self.process_check_timer.start(100)  # 100ms 간격으로 체크
        
        self._connect_signals()
        self.widget.set_controller(self)  # 위젯에 컨트롤러 참조 설정
        logging.debug("[컨트롤러] 초기화 완료")
        
        logging.info("EtcFunctionController 초기화 완료")
        
    def _connect_signals(self):
        """시그널 연결"""
        # 카운트다운 컨트롤러 시그널 연결
        self.countdown_controller.countdown_updated.connect(self._update_countdown_label)
        self.countdown_controller.countdown_finished.connect(self._on_countdown_finished)
        logging.debug("[컨트롤러] 시그널 연결 완료")
        # 카운트다운 값 변경 시그널 연결
        self.widget.countdown_value_changed.connect(self._handle_countdown_value_changed)
        
    def _on_key_pressed(self, key_info):
        """키가 눌렸을 때의 처리"""
        logging.debug(f"[EtcFunctionController] 키 눌림 감지: {key_info}")
        
        if self._is_group_a_key(key_info):
            logging.debug("[EtcFunctionController] A그룹 키 감지됨")
            self._key_state.update({
                'group_a_pressed': True,
                'last_key_info': key_info,
                'sequence_start_time': time.time()
            })
            self._sequence_timer.start()
            
        elif self._is_group_b_key(key_info) and self._key_state['group_a_pressed']:
            logging.debug("[EtcFunctionController] B그룹 키 감지됨 (A그룹 키 활성화 상태)")
            self._key_state['group_b_pressed'] = True
            
    def _on_key_released(self, key_info):
        """키가 떼졌을 때의 처리"""
        logging.debug(f"[EtcFunctionController] 키 뗌 감지: {key_info}")
        
        if self._is_group_b_key(key_info) and self._validate_key_sequence():
            logging.debug("[EtcFunctionController] 유효한 키 시퀀스 감지됨, 카운트다운 시작")
            self._sequence_timer.stop()
            self._start_countdown()
            
    def _is_group_a_key(self, key_info):
        """A그룹 키인지 확인"""
        return key_info['virtual_key'] in [97, 49]  # 숫자패드 1 또는 일반 1
        
    def _is_group_b_key(self, key_info):
        """B그룹 키인지 확인"""
        return key_info['virtual_key'] == 13  # 엔터 키
        
    def _validate_key_sequence(self):
        """키 시퀀스 유효성 검증"""
        if (self._key_state['group_a_pressed'] and 
            self._key_state['group_b_pressed']):
            logging.debug("[EtcFunctionController] 키 시퀀스 검증 성공")
            self._key_state['sequence_valid'] = True
            return True
        logging.debug("[EtcFunctionController] 키 시퀀스 검증 실패")
        return False
        
    def _on_sequence_timeout(self):
        """시퀀스 타임아웃 처리"""
        logging.debug("[EtcFunctionController] 키 시퀀스 타임아웃 발생")
        self._reset_key_state()
        
    def _reset_key_state(self):
        """키 상태 초기화"""
        logging.debug("[EtcFunctionController] 키 상태 초기화")
        self._key_state.update({
            'group_a_pressed': False,
            'group_b_pressed': False,
            'last_key_info': None,
            'sequence_valid': False,
            'sequence_start_time': None
        })
        
    def _check_conditions(self):
        """모든 실행 조건 체크"""
        is_enabled = self.widget.is_logic_enabled
        is_active = self.process_manager.is_selected_process_active()
        is_valid = self._key_state['sequence_valid']
        
        logging.debug(f"[EtcFunctionController] 조건 체크: "
                     f"로직 활성화={is_enabled}, "
                     f"프로세스 활성화={is_active}, "
                     f"시퀀스 유효={is_valid}")
                     
        return is_enabled and is_active and is_valid
        
    def _start_countdown(self):
        """카운트다운 시작"""
        if self._check_conditions():
            logging.debug("[EtcFunctionController] 카운트다운 시작")
            self.countdown_controller.start_countdown()
            self._reset_key_state()
        else:
            logging.debug("[EtcFunctionController] 카운트다운 시작 조건 불충족")
            
    def _on_countdown_finished(self):
        """카운트다운 완료 처리"""
        logging.debug("[EtcFunctionController] 카운트다운 완료")
        self._reset_key_state()
        
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
