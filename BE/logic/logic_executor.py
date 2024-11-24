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
    
    def start_monitoring(self):
        """트리거 키 모니터링 시작"""
        if self.is_executing:
            return
            
        self.keyboard_hook = KeyboardHook()
        self.keyboard_hook.key_pressed.connect(self._on_key_pressed)
        self.keyboard_hook.start()
    
    def stop_monitoring(self):
        """트리거 키 모니터링 중지"""
        if self.keyboard_hook:
            self.keyboard_hook.stop()
            self.keyboard_hook = None
    
    def _on_key_pressed(self, key_info):
        """키 입력 감지 시 호출
        
        Args:
            key_info (dict): 입력된 키 정보
        """
        self.log_message.emit(f"키 입력 감지: {key_info}")  # 키 입력 로그
        
        if not self._should_execute_logic():
            self.log_message.emit("로직 실행 조건이 맞지 않습니다.")  # 실행 조건 로그
            return
        
        self.execute_logic(key_info)
    
    def _should_execute_logic(self):
        """로직 실행 조건 확인
        
        Returns:
            bool: 로직을 실행해야 하는지 여부
        """
        # 이미 실행 중이면 실행하지 않음
        if self.is_executing:
            self.log_message.emit("이미 로직이 실행 중입니다.")
            return False
        
        # 선택된 프로세스와 활성 프로세스가 동일한지 확인
        selected_process = self.process_manager.get_selected_process()
        active_process = self.process_manager.get_active_process()
        
        self.log_message.emit(f"선택된 프로세스: {selected_process}")  # 프로세스 정보 로그
        self.log_message.emit(f"활성 프로세스: {active_process}")
        
        if not selected_process:
            self.log_message.emit("선택된 프로세스가 없습니다.")
            return False
            
        if not active_process:
            self.log_message.emit("활성 프로세스를 가져올 수 없습니다.")
            return False
            
        is_match = selected_process['pid'] == active_process['pid']
        self.log_message.emit(f"프로세스 일치 여부: {is_match}")
        return is_match
    
    def execute_logic(self, key_info):
        """로직 실행"""
        if not self._should_execute_logic():
            self.log_message.emit("로직 실행 조건이 맞지 않습니다.")
            return
            
        # 프로세스 정보 로깅
        selected = self.process_manager.get_selected_process()
        active = self.process_manager.get_active_process()
        self.log_message.emit(f"선택된 프로세스: {selected}")
        self.log_message.emit(f"활성 프로세스: {active}")
        self.log_message.emit(f"프로세스 일치 여부: {self._should_execute_logic()}")
        
        # 키 입력 로깅
        self.log_message.emit(f"키 입력 감지: {key_info}")
        
        # 트리거 키 매칭 확인
        if not self.is_executing:
            # 모든 로직을 가져와서 트리거 키 매칭 확인
            all_logics = self.logic_manager.get_all_logics()
            self.log_message.emit(f"사용 가능한 로직 수: {len(all_logics)}")
            
            for logic_name, logic in all_logics.items():
                self.log_message.emit(f"로직 '{logic_name}' 트리거 키 매칭 시도")
                self.log_message.emit(f"트리거 키: {logic.get('trigger_key')}, 입력 키: {key_info}")
                
                if self._is_trigger_key_matched(logic, key_info):
                    self.selected_logic = logic
                    self.is_executing = True
                    self.current_step_index = 0
                    self.log_message.emit(f"로직 '{logic_name}' 실행 시작")
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
        if not self.is_executing or not self.selected_logic:
            return
            
        steps = self.selected_logic.get('items', [])
        if self.current_step_index < len(steps):
            current_step = steps[self.current_step_index]
            self.log_message.emit(f"스텝 {self.current_step_index + 1} 실행: {current_step.get('display_text')}")
            
            if current_step['type'] == 'key_input':
                self._execute_step(current_step)
                self.current_step_index += 1
                self._execute_next_step()  # 다음 스텝 실행
            elif current_step['type'] == 'delay':
                self._execute_step(current_step)
                self.current_step_index += 1
                self._execute_next_step()  # 다음 스텝 실행
            
            if self.current_step_index >= len(steps):
                self.is_executing = False
                self.log_message.emit(f"로직 '{self.selected_logic.get('name')}' 실행 완료")
                self.selected_logic = None
                self.current_step_index = 0
                
    def _execute_step(self, step):
        """스텝 실행"""
        if step['type'] == 'key_input':
            key_code = step['key_code']
            virtual_key = step['virtual_key']
            scan_code = step['scan_code']
            action = step['action']
            modifiers = step.get('modifiers', 0)
            
            if action == '누르기':
                win32api.keybd_event(virtual_key, scan_code, 0, 0)
            else:  # 떼기
                win32api.keybd_event(virtual_key, scan_code, win32con.KEYEVENTF_KEYUP, 0)
                
        elif step['type'] == 'delay':
            time.sleep(step['duration'])
            
    def _is_trigger_key_matched(self, logic, key_info):
        """트리거 키 매칭 확인"""
        trigger_key = logic.get('trigger_key', {})
        self.log_message.emit(f"트리거 키 매칭 확인 - 트리거 키: {trigger_key}, 입력 키: {key_info}")
        
        # modifiers가 enum인 경우 정수값으로 변환
        key_modifiers = key_info.get('modifiers')
        if hasattr(key_modifiers, 'value'):
            key_modifiers = key_modifiers.value
        else:
            key_modifiers = key_info.get('modifiers', 0)
            
        return (trigger_key.get('virtual_key') == key_info.get('virtual_key') and
                trigger_key.get('scan_code') == key_info.get('scan_code') and
                trigger_key.get('modifiers', 0) == key_modifiers)
        
    def _is_key_matched(self, key_config, key_info):
        """키 매칭 확인"""
        if not key_config or not key_info:
            return False
            
        self.log_message.emit(f"키 매칭 확인 - 설정 키: {key_config}, 입력 키: {key_info}")
        return (key_config.get('virtual_key') == key_info.get('virtual_key') and
                key_config.get('scan_code') == key_info.get('scan_code') and
                key_config.get('modifiers', 0) == key_info.get('modifiers', 0))
