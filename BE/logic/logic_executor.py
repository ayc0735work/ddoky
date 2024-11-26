import time
import win32api
import win32con
from PySide6.QtCore import QObject, Signal
from ..utils.key_handler import KeyboardHook

class LogicExecutor(QObject):
    """로직 실행기"""
    
    # 시그널 정의
    execution_started = Signal()  # 로직 실행 시작
    execution_finished = Signal()  # 로직 실행 완료
    execution_error = Signal(str)  # 실행 중 오류 발생
    log_message = Signal(str)  # 로그 메시지 시그널 추가
    
    def __init__(self, process_manager, logic_manager):
        """초기화
        
        Args:
            process_manager: 프로세스 관리자 인스턴스
            logic_manager: 로직 관리자 인스턴스
        """
        super().__init__()
        self.process_manager = process_manager
        self.logic_manager = logic_manager
        self.keyboard_hook = None
        self.selected_logic = None
        self.is_executing = False
        self.current_step_index = 0
        self.execution_stack = []  # 실행 중인 로직 스택
        self.MAX_EXECUTION_DEPTH = 5  # 최대 중첩 깊이

    def start_monitoring(self):
        """트리거 키 모니터링 시작"""
        if self.is_executing:
            return
            
        self.keyboard_hook = KeyboardHook()
        self.keyboard_hook.key_released.connect(self._on_key_released)  # 키를 뗄 때 이벤트 연결
        self.keyboard_hook.start()
    
    def stop_monitoring(self):
        """트리거 키 모니터링 중지"""
        if self.keyboard_hook:
            self.keyboard_hook.stop()
            self.keyboard_hook = None
    
    def _on_key_released(self, key_info):
        """키를 뗄 때 호출
        
        Args:
            key_info (dict): 입력된 키 정보
        """
        self.log_message.emit(f"키 입력 감지: {key_info}")
        
        if not self._should_execute_logic():
            self.log_message.emit("로직 실행 조건이 맞지 않습니다.")
            return
        
        # 로직 찾기 및 실행
        for logic_name, logic in self.logic_manager.get_all_logics().items():
            self.log_message.emit(f"트리거 키: {logic.get('trigger_key', {})}, 입력 키: {key_info}")
            if self._is_trigger_key_matched(logic, key_info):
                self.selected_logic = logic
                self.is_executing = True
                self.current_step_index = 0
                self.log_message.emit(f"로직 '{logic_name}' 실행 시작")
                self.stop_monitoring()  # 로직 실행 중에는 키 입력 감지를 하지 않도록 중지
                self._execute_next_step()  # 첫 번째 스텝 실행
                return
            
        self.log_message.emit("일치하는 트리거 키를 찾을 수 없습니다.")
    
    def _should_execute_logic(self):
        """로직 실행 조건 확인
        
        Returns:
            bool: 로직을 실행해야 하는지 여부
        """
        # 이미 실행 중이면 실행하지 않음
        if self.is_executing:
            return False
        
        # 선택된 프로세스와 활성 프로세스가 동일한지 확인
        selected_process = self.process_manager.get_selected_process()
        active_process = self.process_manager.get_active_process()
        
        if not selected_process:
            self.log_message.emit("선택된 프로세스가 없습니다.")
            return False
            
        if not active_process:
            self.log_message.emit("활성 프로세스를 가져올 수 없습니다.")
            return False
            
        is_match = selected_process['pid'] == active_process['pid']
        return is_match
    
    def execute_logic(self, key_info):
        """로직 실행"""
        if not self._should_execute_logic():
            self.log_message.emit("로직 실행 조건이 맞지 않습니다.")
            return
            
        # 트리거 키 정보 저장
        self.trigger_key_info = key_info
            
        # 프로세스 정보 로깅
        selected = self.process_manager.get_selected_process()
        active = self.process_manager.get_active_process()
        self.log_message.emit(f"선택된 프로세스: {selected}")
        self.log_message.emit(f"활성 프로세스: {active}")
        
        # 로직 찾기 및 실행
        for logic_name, logic in self.logic_manager.get_all_logics().items():
            self.log_message.emit(f"트리거 키: {logic.get('trigger_key', {})}, 입력 키: {key_info}")
            if self._is_trigger_key_matched(logic, key_info):
                self.selected_logic = logic
                self.is_executing = True
                self.current_step_index = 0
                self.current_repeat = 1  # 현재 반복 횟수 초기화
                repeat_count = logic.get('repeat_count', 1)
                self.log_message.emit(f"로직 '{logic_name}' 실행 시작 (총 {repeat_count}회 반복)")
                self.stop_monitoring()  # 로직 실행 중에는 키 입력 감지를 하지 않도록 중지
                
                # 트리거 키를 떼는 동작 추가
                virtual_key = key_info['virtual_key']
                scan_code = key_info['scan_code']
                win32api.keybd_event(virtual_key, scan_code, win32con.KEYEVENTF_KEYUP, 0)
                
                self._execute_next_step()  # 첫 번째 스텝 실행
                return
            
        self.log_message.emit("일치하는 트리거 키를 찾을 수 없습니다.")
        
        # 로직 실행 중이면 다음 스텝 키 매칭 확인
        if self.is_executing and self.selected_logic:
            steps = self.selected_logic.get('items', [])
            if self.current_step_index < len(steps):
                current_step = steps[self.current_step_index]
                if current_step['type'] == 'key_input' and self._is_key_matched(current_step, key_info):
                    self.log_message.emit(f"스텝 {self.current_step_index + 1} 실행: {current_step.get('display_text')}")
                    self._execute_step(current_step)
                    self.current_step_index += 1
                    self._execute_next_step()  # 다음 스텝 실행
                    
                if self.current_step_index >= len(steps):
                    self.is_executing = False
                    self.log_message.emit(f"로직 '{self.selected_logic.get('name')}' 실행 완료")
                    self.selected_logic = None
                    self.current_step_index = 0
                    
    def _execute_next_step(self):
        """다음 스텝 실행"""
        if not self.selected_logic or not self.is_executing:
            return
            
        items = self.selected_logic.get('items', [])
        
        # 모든 스텝이 완료되었는지 확인
        if self.current_step_index >= len(items):
            # 반복 횟수 확인
            repeat_count = self.selected_logic.get('repeat_count', 1)
            current_repeat = getattr(self, 'current_repeat', 1)
            
            if current_repeat < repeat_count:
                # 아직 반복 횟수가 남았으면 처음부터 다시 시작
                self.current_step_index = 0
                self.current_repeat = current_repeat + 1
                self.log_message.emit(f"로직 반복 {self.current_repeat}/{repeat_count} 시작")
                self._execute_next_step()
                return
            
            # 현재 로직 완료, 이전 로직으로 복원
            if self.execution_stack:
                self.log_message.emit(f"중첩 로직 '{self.selected_logic.get('name')}' 실행 완료")
                self._restore_execution_state()
                self._execute_next_step()
            else:
                # 모든 로직 실행 완료
                self.log_message.emit(f"로직 '{self.selected_logic.get('name')}' 실행 완료")
                self.is_executing = False
                self.selected_logic = None
                self.current_step_index = 0
                self.current_repeat = 1
                self.start_monitoring()
            return
            
        # 현재 스텝 실행
        current_step = items[self.current_step_index]
        self.current_step_index += 1
        self._execute_step(current_step)
        
    def _execute_step(self, step):
        """스텝 실행"""
        self.log_message.emit(f"스텝 {self.current_step_index} 실행: {step['display_text']}")
        
        if step['type'] == 'key_input':
            self.log_message.emit(f"키 입력 실행: {step['key_code']} - {step['action']}")
            self.log_message.emit(f"키 상세 정보 - virtual_key: {step['virtual_key']}, scan_code: {step['scan_code']}")
            
            # 키 코드를 가상 키 코드로 변환
            virtual_key = step['virtual_key']
            scan_code = step['scan_code']
            
            # 콤마 키 특수 처리
            if step['key_code'] == ',' and virtual_key in [44, 188]:
                virtual_key = 0xBC  # VK_OEM_COMMA (188)
                scan_code = 51  # 콤마 키의 스캔 코드
            
            # 확장 키 플래그 설정
            flags = 0
            if step['key_code'] == '숫자패드 엔터' or scan_code > 0xFF:
                flags |= win32con.KEYEVENTF_EXTENDEDKEY
            
            if step['action'] == '누르기':
                win32api.keybd_event(virtual_key, scan_code, flags, 0)
            else:  # 떼기
                win32api.keybd_event(virtual_key, scan_code, flags | win32con.KEYEVENTF_KEYUP, 0)
                
        elif step['type'] == 'delay':
            duration = float(step['duration'])
            self.log_message.emit(f"지연 시간 실행: {duration}초")
            time.sleep(duration)
            
        elif step['type'] == 'logic':
            # 중첩 로직 실행
            if len(self.execution_stack) >= self.MAX_EXECUTION_DEPTH:
                self.log_message.emit("최대 중첩 깊이에 도달했습니다.")
                return
                
            logic_id = step.get('logic_id')
            if not logic_id:
                self.log_message.emit("로직 ID가 지정되지 않았습니다.")
                return
                
            # 현재 실행 상태 저장
            self.execution_stack.append({
                'logic': self.selected_logic,
                'step_index': self.current_step_index,
                'repeat': getattr(self, 'current_repeat', 1)
            })
            
            # 중첩 로직 실행
            nested_logic = self.logic_manager.get_all_logics().get(logic_id)
            if nested_logic:
                self.selected_logic = nested_logic
                self.current_step_index = 0
                self.current_repeat = 1
                repeat_count = step.get('repeat_count', 1)
                self.log_message.emit(f"중첩 로직 '{nested_logic.get('name')}' 실행 시작 (총 {repeat_count}회 반복)")
                self._execute_next_step()
            else:
                self.log_message.emit(f"로직 ID '{logic_id}'를 찾을 수 없습니다.")
                # 이전 상태로 복원
                self._restore_execution_state()
        
        # 다음 스텝 실행
        self._execute_next_step()

    def _restore_execution_state(self):
        """실행 상태 복원"""
        if self.execution_stack:
            state = self.execution_stack.pop()
            self.selected_logic = state['logic']
            self.current_step_index = state['step_index']
            self.current_repeat = state['repeat']

    def _is_trigger_key_matched(self, logic, key_info):
        """트리거 키 매칭 확인"""
        trigger_key = logic.get('trigger_key', {})
        self.log_message.emit(f"트리거 키 매칭 확인 - 트리거 키: {trigger_key}, 입력 키: {key_info}")
        
        # 가상 키와 스캔 코드만 비교
        return (trigger_key.get('virtual_key') == key_info.get('virtual_key') and
                trigger_key.get('scan_code') == key_info.get('scan_code'))
        
    def _is_key_matched(self, key_config, key_info):
        """키 매칭 확인"""
        if not key_config or not key_info:
            return False
            
        self.log_message.emit(f"키 매칭 확인 - 설정 키: {key_config}, 입력 키: {key_info}")
        return (key_config.get('virtual_key') == key_info.get('virtual_key') and
                key_config.get('scan_code') == key_info.get('scan_code') and
                key_config.get('modifiers', 0) == key_info.get('modifiers', 0))

    def stop_all_logic(self):
        """모든 실행 중인 로직을 강제로 중지"""
        if self.is_executing:
            self.log_message.emit("모든 실행 중인 로직을 중지합니다.")
            self.is_executing = False
            self.selected_logic = None
            self.current_step_index = 0
            self.current_repeat = 1
            self.execution_stack.clear()  # 실행 스택 초기화
            self.start_monitoring()  # 모니터링 재시작
