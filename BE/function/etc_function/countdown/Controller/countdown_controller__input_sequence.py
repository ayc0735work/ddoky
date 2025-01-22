"""
기타 기능 컨트롤러 모듈

이 모듈은 다양한 기타 기능들을 관리하는 컨트롤러를 제공합니다.
주요 기능:
1. 키 입력 시퀀스 관리 (일반/탭 시퀀스)
2. 카운트다운 제어
3. 프로세스 상태 관리

작동 방식:
1. 키 입력 감지 및 시퀀스 분류
2. 시퀀스 유효성 검사
3. 카운트다운 컨트롤러와 연동
4. 프로세스 매니저와 연동
"""

import logging
import sys
import time
from PySide6.QtCore import QTimer, QObject
from BE.function._common_components.window_process_handler import ProcessManager
from BE.function.etc_function.countdown.Controller.countdown_controller__main import CountdownController

# 로깅 설정
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class CountdownControllerInputSequence(QObject):
    """기타 기능 컨트롤러 클래스
    
    키 입력을 감지하고 적절한 동작을 수행하는 컨트롤러입니다.
    
    시퀀스 종류:
    1. 일반 시퀀스: 1 + 엔터
    2. 탭 시퀀스: 탭 + 1 (10초 이내)
    
    주요 기능:
        - 키 입력 시퀀스 관리
        - 카운트다운 제어
        - 프로세스 상태 관리
    """
    
    def __init__(self, widget):
        super().__init__()
        logging.debug("[컨트롤러] 초기화 시작")
        self.widget = widget
        self.process_manager = ProcessManager()
        self.countdown_controller = CountdownController()
        
        # 키 상태 관리
        self._key_state = {
            'group_a_pressed': False,     # A그룹 키(1) 눌림 상태
            'group_b_pressed': False,     # B그룹 키(엔터) 눌림 상태
            'last_key_info': None,        # 마지막 키 정보
            'sequence_valid': False,       # 일반 시퀀스 유효성
            'sequence_start_time': None,   # 시퀀스 시작 시간
            'tab_pressed_time': None,      # 탭키 눌린 시간
            'tab_sequence_used': False,    # 탭 시퀀스 사용 여부
            'tab_cooldown_time': None      # 탭 시퀀스 쿨다운 시간
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
        
        logging.info("CountdownControllerInputSequence 초기화 완료")
        
    def _connect_signals(self):
        """시그널 연결"""
        # 카운트다운 컨트롤러 시그널 연결
        self.countdown_controller.countdown_updated.connect(self._update_countdown_label)
        self.countdown_controller.countdown_finished.connect(self._on_countdown_finished)
        logging.debug("[컨트롤러] 시그널 연결 완료")
        # 카운트다운 값 변경 시그널 연결
        self.widget.countdown_value_changed.connect(self._handle_countdown_value_changed)
        
    def _is_tab_key(self, key_info):
        """탭 키인지 확인
        
        Args:
            key_info: 키 정보 객체
            
        Returns:
            bool: 탭 키인 경우 True
        """
        return (key_info['virtual_key'] == 9 and 
                key_info['key_code'] == 'Tab' and 
                not key_info['is_system_key'])
                
    def _on_key_pressed(self, key_info):
        """키가 눌렸을 때의 처리
        
        동작 순서:
        1. 탭키 처리
        2. A그룹 키(숫자1) 처리
        3. B그룹 키(엔터) 처리
        """
        logging.debug(f"[CountdownControllerInputSequence] 키 눌림 감지: {key_info}")
        current_time = time.time()
        
        # 1. 탭키 처리
        if self._is_tab_key(key_info):
            self._key_state.update({
                'tab_pressed_time': current_time,
                'tab_sequence_used': False  # 탭 시퀀스 초기화
            })
            logging.debug("[CountdownControllerInputSequence] 탭키 감지됨, 시퀀스 초기화")
            return
            
        # 2. A그룹 키(숫자1) 처리
        elif self._is_group_a_key(key_info):
            # 2-1. 탭 시퀀스 체크
            if (not self._key_state['tab_sequence_used'] and  # 아직 사용되지 않은 탭 시퀀스
                self._key_state['tab_pressed_time'] and       # 탭이 눌린 적이 있고
                current_time - self._key_state['tab_pressed_time'] <= 10):  # 10초 이내
                
                self._key_state['tab_sequence_used'] = True  # 탭 시퀀스 사용 처리
                self._key_state['tab_cooldown_time'] = current_time  # 쿨다운 시작
                logging.debug("[CountdownControllerInputSequence] 탭 시퀀스로 카운트다운 시작")
                self.start_hellfire_countdown()
                return
                
            # 2-2. 일반 시퀀스 시작
            if not self._key_state['tab_sequence_used']:  # 탭 시퀀스가 사용되지 않은 경우에만
                self._key_state.update({
                    'group_a_pressed': True,
                    'last_key_info': key_info,
                    'sequence_start_time': current_time
                })
                self._sequence_timer.start()
                logging.debug("[CountdownControllerInputSequence] 일반 시퀀스 시작")
                
        # 3. B그룹 키(엔터) 처리
        elif self._is_group_b_key(key_info) and self._key_state['group_a_pressed']:
            logging.debug("[CountdownControllerInputSequence] B그룹 키 감지됨 (A그룹 키 활성화 상태)")
            self._key_state['group_b_pressed'] = True
            
    def _on_key_released(self, key_info):
        """키가 떼졌을 때의 처리
        
        동작 순서:
        1. B그룹 키(엔터) 처리
        2. 시퀀스 유효성 검사
        3. 카운트다운 시작
        """
        logging.debug(f"[CountdownControllerInputSequence] 키 뗌 감지: {key_info}")
        
        if self._is_group_b_key(key_info) and self._validate_key_sequence():
            logging.debug("[CountdownControllerInputSequence] 유효한 키 시퀀스 감지됨, 카운트다운 시작")
            self._sequence_timer.stop()
            self.start_hellfire_countdown()
            
    def _is_group_a_key(self, key_info):
        """A그룹 키인지 확인
        
        Args:
            key_info: 키 정보 객체
            
        Returns:
            bool: A그룹 키인 경우 True
        """
        return key_info['virtual_key'] in [97, 49]  # 숫자패드 1 또는 일반 1
        
    def _is_group_b_key(self, key_info):
        """B그룹 키인지 확인
        
        Args:
            key_info: 키 정보 객체
            
        Returns:
            bool: B그룹 키인 경우 True
        """
        return key_info['virtual_key'] == 13  # 엔터 키
        
    def _validate_key_sequence(self):
        """키 시퀀스 유효성 검증
        
        시퀀스 유효성 조건:
        - A그룹 키가 눌렸고
        - B그룹 키가 눌렸고
        - 시퀀스 시작 시간이 존재
        """
        if (self._key_state['group_a_pressed'] and 
            self._key_state['group_b_pressed']):
            logging.debug("[CountdownControllerInputSequence] 키 시퀀스 검증 성공")
            self._key_state['sequence_valid'] = True
            return True
        logging.debug("[CountdownControllerInputSequence] 키 시퀀스 검증 실패")
        return False
        
    def _on_sequence_timeout(self):
        """시퀀스 타임아웃 처리
        
        동작 순서:
        1. 키 상태 초기화
        """
        logging.debug("[CountdownControllerInputSequence] 키 시퀀스 타임아웃 발생")
        self._reset_key_state()
        
    def _reset_key_state(self):
        """키 상태 초기화
        
        동작 순서:
        1. 키 상태 초기화
        2. 탭 시퀀스 쿨다운 체크
        """
        logging.debug("[CountdownControllerInputSequence] 키 상태 초기화")
        current_time = time.time()
        
        # 탭 시퀀스 쿨다운 체크
        if (self._key_state['tab_cooldown_time'] and 
            current_time - self._key_state['tab_cooldown_time'] > 10):  # 10초 쿨다운
            self._key_state['tab_sequence_used'] = False
            logging.debug("[CountdownControllerInputSequence] 탭 시퀀스 쿨다운 완료")
        
        self._key_state.update({
            'group_a_pressed': False,
            'group_b_pressed': False,
            'last_key_info': None,
            'sequence_valid': False,
            'sequence_start_time': None,
            'tab_pressed_time': None
        })
        
    def _check_process_state(self):
        """프로세스 상태 체크
        
        동작 순서:
        1. 프로세스 상태 검사
        2. 카운트다운 중지 (비활성화 시)
        """
        try:
            # 프로세스가 비활성화되었을 때만 카운트다운 중지
            if not self.process_manager.is_selected_process_active():
                if self.countdown_controller.is_running():
                    logging.info("[컨트롤러] 프로세스 비활성화로 카운트다운 중지")
                    self.stop_hellfire_countdown()
                    
        except Exception as e:
            logging.error(f"[컨트롤러] 프로세스 상태 체크 중 오류 발생: {e}")
            
    def _start_countdown(self):
        """카운트다운 시작
        
        동작 순서:
        1. 조건 체크
        2. 카운트다운 시작
        """
        if self._check_conditions():
            logging.debug("[CountdownControllerInputSequence] 카운트다운 시작")
            self.countdown_controller.start_countdown()
            self._reset_key_state()
        else:
            logging.debug("[CountdownControllerInputSequence] 카운트다운 시작 조건 불충족")
            
    def _on_countdown_finished(self):
        """카운트다운 완료 처리
        
        동작 순서:
        1. 키 상태 초기화
        """
        logging.debug("[CountdownControllerInputSequence] 카운트다운 완료")
        self._reset_key_state()
        
    def _handle_countdown_value_changed(self, value):
        """카운트다운 값 변경 처리
        
        동작 순서:
        1. 카운트다운 값 변경
        """
        # 여기서 필요한 추가 처리를 할 수 있습니다.
        pass
        
    def get_countdown_value(self):
        """현재 설정된 카운트다운 값을 반환
        
        Returns:
            int: 현재 설정된 카운트다운 값
        """
        return self.widget.countdown_spinbox.value()
        
    def start_hellfire_countdown(self):
        """헬파이어 카운트다운 시작
        
        동작 순서:
        1. 프로세스 상태 검사
        2. 카운트다운 컨트롤러에 시작 요청
        3. 로그 기록
        
        주의사항:
            프로세스가 실행 중일 때는 카운트다운을 시작하지 않음
        """
        if not self.process_manager.is_selected_process_active():
            logging.info("[컨트롤러] 프로세스가 활성화되지 않음, 카운트다운 시작 불가")
            return
            
        logging.info("[컨트롤러] 헬파이어 카운트다운 시작 요청")
        logging.info("헬파이어 카운트다운 시작")
        
        if self.countdown_controller.is_running():
            # 이미 실행 중이면 리셋
            self.countdown_controller.reset_countdown()
        else:
            # 처음 시작
            self.countdown_controller.start_countdown()
            
    def stop_hellfire_countdown(self):
        """헬파이어 카운트다운 중지
        
        동작 순서:
        1. 카운트다운 컨트롤러에 중지 요청
        2. 로그 기록
        """
        logging.info("[컨트롤러] 헬파이어 카운트다운 중지 요청")
        logging.info("헬파이어 카운트다운 중지")
        self.countdown_controller.stop_countdown()

    def _update_countdown_label(self, value):
        """카운트다운 레이블 업데이트
        
        Args:
            value (float): 현재 카운트다운 값 (초)
        """
        self.widget.update_hellfire_countdown_label(f"{value:.2f}")

    def _check_conditions(self):
        """모든 실행 조건 체크
        
        조건:
        - 로직 활성화
        - 프로세스 활성화
        - 시퀀스 유효성
        """
        is_enabled = self.widget.is_logic_enabled
        is_active = self.process_manager.is_selected_process_active()
        is_valid = self._key_state['sequence_valid']
        
        logging.debug(f"[CountdownControllerInputSequence] 조건 체크: "
                     f"로직 활성화={is_enabled}, "
                     f"프로세스 활성화={is_active}, "
                     f"시퀀스 유효={is_valid}")
                     
        return is_enabled and is_active and is_valid
