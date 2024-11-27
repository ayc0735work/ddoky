import time
import win32api
import win32con
from PySide6.QtCore import QObject, Signal, QTimer
from ..utils.key_handler import KeyboardHook
import threading

class LogicExecutor(QObject):
    """로직 실행기"""
    
    # 시그널 정의
    execution_started = Signal()  # 로직 실행 시작
    execution_finished = Signal()  # 로직 실행 완료
    execution_error = Signal(str)  # 실행 중 오류 발생
    log_message = Signal(str)  # 로그 메시지 시그널
    execution_state_changed = Signal(dict)  # 상태 변경 알림
    
    def __init__(self, process_manager, logic_manager):
        """초기화
        
        Args:
            process_manager: 프로세스 관리자 인스턴스
            logic_manager: 로직 관리자 인스턴스
        """
        super().__init__()
        self.process_manager = process_manager
        self.logic_manager = logic_manager
        
        # 상태 관리
        self.execution_state = {
            'is_executing': False,
            'is_stopping': False,
            'current_step': 0,
            'current_repeat': 1
        }
        
        # 리소스 관리
        self.keyboard_hook = None
        self.selected_logic = None
        self.timer = QTimer()
        
        # 동기화를 위한 락
        self._hook_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._cleanup_lock = threading.Lock()
        
        # 로직 스택 (중첩 로직 처리용)
        self._logic_stack = []
        
        # 시작 시간 저장
        self._start_time = time.time()
    
    def _update_state(self, **kwargs):
        """상태 업데이트 및 알림"""
        with self._state_lock:
            self.execution_state.update(kwargs)
            self.execution_state_changed.emit(self.execution_state.copy())
    
    def start_monitoring(self):
        """트리거 키 모니터링 시작"""
        with self._hook_lock:
            if self.execution_state['is_executing'] or self.keyboard_hook:
                return
                
            try:
                self.keyboard_hook = KeyboardHook()
                self.keyboard_hook.key_released.connect(self._on_key_released)
                self.keyboard_hook.start()
                self._log_with_time("키보드 모니터링 시작")
            except Exception as e:
                self._log_with_time(f"키보드 모니터링 시작 실패: {str(e)}")
                self._safe_cleanup()
    
    def stop_monitoring(self):
        """트리거 키 모니터링 중지"""
        with self._hook_lock:
            if self.keyboard_hook:
                try:
                    self.keyboard_hook.stop()
                    self.keyboard_hook.key_released.disconnect()
                    self.keyboard_hook = None
                    self._log_with_time("키보드 모니터링 중지")
                except Exception as e:
                    self._log_with_time(f"키보드 모니터링 중지 실패: {str(e)}")
    
    def _safe_cleanup(self):
        """안전한 정리 작업"""
        with self._cleanup_lock:
            try:
                if self.timer and self.timer.isActive():
                    self.timer.stop()
                    
                with self._hook_lock:
                    if self.keyboard_hook:
                        self.keyboard_hook.stop()
                        self.keyboard_hook.key_released.disconnect()
                        self.keyboard_hook = None
                        
                # 상태 초기화
                self._update_state(
                    is_executing=False,
                    is_stopping=False,
                    current_step=0,
                    current_repeat=1
                )
                
            except Exception as e:
                self._log_with_time(f"정리 작업 중 오류 발생: {str(e)}")
            finally:
                self.selected_logic = None
    
    def _on_key_released(self, key_info):
        """키를 뗄 때 호출
        
        Args:
            key_info (dict): 입력된 키 정보
        """
        self._log_with_time(f"키 입력 감지: {key_info}")
        
        if not self._should_execute_logic():
            self._log_with_time("로직 실행 조건이 맞지 않습니다.")
            return
            
        # 로직 찾기 및 실행
        for logic_name, logic in self.logic_manager.get_all_logics().items():
            if self._is_trigger_key_matched(logic, key_info):
                try:
                    self.selected_logic = logic
                    self._update_state(
                        is_executing=True,
                        current_step=0,
                        current_repeat=1
                    )
                    # 로직 실행 시작 시 시간 초기화
                    self._start_time = time.time()
                    self._log_with_time(f"로직 '{logic_name}' 실행 시작")
                    
                    self.stop_monitoring()
                    self.execution_started.emit()
                    
                    # 비동기적으로 첫 번째 스텝 실행
                    self.timer.singleShot(0, self._execute_next_step)
                    return
                    
                except Exception as e:
                    self._log_with_time(f"로직 시작 중 오류 발생: {str(e)}")
                    self._safe_cleanup()
                    
        self._log_with_time("일치하는 트리거 키를 찾을 수 없습니다.")
    
    def _execute_next_step(self):
        """현재 실행할 스텝이 무엇인지 결정하는 관리자 함수"""
        if not self.selected_logic or self.execution_state['is_stopping']:
            return
            
        try:
            items = self.selected_logic.get('items', [])
            current_step = self.execution_state['current_step']
            
            # 모든 스텝이 완료되었는지 확인
            if current_step >= len(items):
                repeat_count = self.selected_logic.get('repeat_count', 1)
                current_repeat = self.execution_state['current_repeat']
                
                self._log_with_time(f"현재 {current_repeat}/{repeat_count} 반복 완료")
                
                if current_repeat < repeat_count:
                    # 아직 반복 횟수가 남았으면 처음부터 다시 시작
                    self._update_state(
                        current_step=0,
                        current_repeat=current_repeat + 1
                    )
                    self.timer.singleShot(100, self._execute_next_step)
                else:
                    # 현재 로직 완료
                    self._log_with_time(f"로직 '{self.selected_logic.get('name')}' 실행 완료")
                    
                    # 스택에 이전 로직이 있으면 복원
                    if self._logic_stack:
                        prev_logic, prev_state = self._logic_stack.pop()
                        self.selected_logic = prev_logic
                        self._update_state(**prev_state)
                        self.timer.singleShot(100, self._execute_next_step)
                    else:
                        # 모든 로직 실행 완료
                        self._safe_cleanup()
                        self.execution_finished.emit()
                        self.start_monitoring()
                return
                
            # 현재 스텝 실행
            step = items[current_step]
            self._update_state(current_step=current_step + 1)
            self._execute_step(step)
            
        except Exception as e:
            self._log_with_time(f"다음 스텝 실행 중 오류 발생: {str(e)}")
            self._safe_cleanup()
    
    def _execute_step(self, step):
        """실제로 해당 스텝이 가지고 있는 어떤 동작을 수행하는 작업자 함수"""
        if self.execution_state['is_stopping']:
            return
            
        try:
            self._log_with_time(f"스텝 {self.execution_state['current_step']} 실행: {step['display_text']}")
            
            if step['type'] == 'key_input':
                self._execute_key_input(step)
                # 키 입력의 경우 키를 누르고 떼는 동작 사이에 약간의 지연 필요
                self.timer.singleShot(20, self._execute_next_step)  # 키 입력 누르기 떼기 모두 지연시간 거친 후 다음 스텝
            elif step['type'] == 'delay':
                self._execute_delay(step)
                # delay 타입은 _execute_delay에서 다음 스텝을 예약함
            elif step['type'] == 'logic':
                self._execute_nested_logic(step)
                # 중첩 로직 실행 후에도 20ms 지연
                self.timer.singleShot(20, self._execute_next_step)
                
        except Exception as e:
            self._log_with_time(f"스텝 실행 중 오류 발생: {str(e)}")
            self._safe_cleanup()
    
    def _execute_key_input(self, step):
        """키 입력 실행"""
        try:
            virtual_key = step['virtual_key']
            scan_code = step['scan_code']
            flags = 0
            
            # 확장 키 플래그 설정
            if step['key_code'] == '숫자패드 엔터' or scan_code > 0xFF:
                flags |= win32con.KEYEVENTF_EXTENDEDKEY
            
            if step['action'] == '누르기':
                win32api.keybd_event(virtual_key, scan_code, flags, 0)
            else:  # 떼기
                win32api.keybd_event(virtual_key, scan_code, flags | win32con.KEYEVENTF_KEYUP, 0)
                
        except Exception as e:
            raise Exception(f"키 입력 실행 실패: {str(e)}")
    
    def _execute_delay(self, step):
        """지연 시간 실행"""
        try:
            duration = float(step['duration'])
            self._log_with_time(f"{duration}초 대기 시작")
            # 지연시간 후에 다음 스텝 실행
            self.timer.singleShot(int(duration * 1000), self._execute_next_step)
        except Exception as e:
            raise Exception(f"지연 시간 실행 실패: {str(e)}")
    
    def stop_all_logic(self):
        """모든 실행 중인 로직을 강제로 중지"""
        self._update_state(is_stopping=True)
        self._log_with_time("모든 실행 중인 로직을 강제로 중지합니다")
        self._safe_cleanup()
        self.start_monitoring()
    
    def __del__(self):
        """소멸자"""
        self._safe_cleanup()

    def _should_execute_logic(self):
        """로직 실행 조건 확인
        
        Returns:
            bool: 로직을 실행해야 하는지 여부
        """
        # 이미 실행 중이면 실행하지 않음
        if self.execution_state['is_executing']:
            return False
        
        # 선택된 프로세스와 활성 프로세스가 동일한지 확인
        selected_process = self.process_manager.get_selected_process()
        active_process = self.process_manager.get_active_process()
        
        if not selected_process:
            self._log_with_time("선택된 프로세스가 없습니다.")
            return False
            
        if not active_process:
            self._log_with_time("활성 프로세스를 가져올 수 없습니다.")
            return False
            
        is_match = selected_process['pid'] == active_process['pid']
        return is_match

    def _is_trigger_key_matched(self, logic, key_info):
        """트리거 키 매칭 확인"""
        trigger_key = logic.get('trigger_key', {})
        self._log_with_time(f"트리거 키 매칭 확인 - 트리거 키: {trigger_key}, 입력 키: {key_info}")
        
        # 가상 키와 스캔 코드만 비교
        return (trigger_key.get('virtual_key') == key_info.get('virtual_key') and
                trigger_key.get('scan_code') == key_info.get('scan_code'))

    def _execute_nested_logic(self, step):
        """중첩 로직 실행"""
        logic_id = step.get('logic_id')
        if not logic_id:
            self._log_with_time("로직 ID가 지정되지 않았습니다.")
            return
            
        nested_logic = self.logic_manager.get_all_logics().get(logic_id)
        if not nested_logic:
            self._log_with_time(f"로직 ID '{logic_id}'를 찾을 수 없습니다.")
            return
            
        # 현재 실행 상태 저장
        current_state = {
            'current_step': self.execution_state['current_step'],
            'current_repeat': self.execution_state['current_repeat'],
            'is_executing': self.execution_state['is_executing'],
            'is_stopping': self.execution_state['is_stopping']
        }
        self._logic_stack.append((self.selected_logic, current_state))
        
        # 중첩 로직 설정 (깊은 복사로 새로운 인스턴스 생성)
        nested_logic = dict(nested_logic)  # 원본 로직을 변경하지 않도록 복사
        self.selected_logic = nested_logic
        
        # 새로운 상태로 시작
        self._update_state(
            current_step=0,
            current_repeat=1,
            is_executing=True,
            is_stopping=False
        )
        
        self._log_with_time(f"중첩 로직 '{nested_logic.get('name')}' 실행 시작 (총 {nested_logic.get('repeat_count', 1)}회 반복)")
        # 중첩 로직은 즉시 시작 (지연은 각 스텝에서 처리)
        self._execute_next_step()

    def _log_with_time(self, message):
        """시간 정보가 포함된 로그 메시지 출력"""
        elapsed = int((time.time() - self._start_time) * 1000)  # 밀리초 단위
        self.log_message.emit(f"[{elapsed}ms] {message}")
