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
    cleanup_finished = Signal()  # 정리 완료 시그널
    
    def __init__(self, process_manager, logic_manager):
        """초기화
        
        Args:
            process_manager: 프로세스 관리자 인스턴스
            logic_manager: 로직 관리자 인스턴스
        """
        super().__init__()
        self.process_manager = process_manager
        self.logic_manager = logic_manager
        
        # 로직 활성화 상태 추가
        self.is_logic_enabled = True
        
        # 상태 관리
        self.execution_state = {
            'is_executing': False,
            'is_stopping': False,
            'current_step': 0,
            'current_repeat': 1
        }
        
        # 키 입력 지연 시간 (초)
        self.KEY_INPUT_DELAY = 0.022
        
        # 리소스 관리
        self.keyboard_hook = None
        self.selected_logic = None
        
        # 동기화를 위한 락
        self._hook_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._cleanup_lock = threading.Lock()
        
        # 로직 스택 (중첩 로직 처리용)
        self._logic_stack = []
        
        # 시작 시간 저장
        self._start_time = time.time()
        
        # 활성 타이머 추적
        self._active_timers = []

    def _update_state(self, **kwargs):
        """상태 업데이트 및 알림"""
        self._log_with_time("[로그] 상태 업데이트 시작: {}".format(kwargs))
        with self._state_lock:
            self._log_with_time("[로그] 상태 락 획득")
            self.execution_state.update(kwargs)
            self._log_with_time("[로그] 새로운 상태: {}".format(self.execution_state))
            self.execution_state_changed.emit(self.execution_state.copy())
            self._log_with_time("[로그] 상태 변경 알림 완료")
    
    def start_monitoring(self):
        """트리거 키 모니터링 시작"""
        with self._hook_lock:
            if self.execution_state['is_executing'] or self.keyboard_hook:
                return
                
            try:
                self.keyboard_hook = KeyboardHook()
                self.keyboard_hook.key_released.connect(self._on_key_released)
                self.keyboard_hook.start()
                self._log_with_time("[로그] 키보드 모니터링 시작")
            except Exception as e:
                self._log_with_time("[오류] 키보드 모니터링 시작 실패: {}".format(str(e)))
                self._safe_cleanup()
    
    def stop_monitoring(self):
        """트리거 키 모니터링 중지"""
        with self._hook_lock:
            if self.keyboard_hook:
                try:
                    self.keyboard_hook.stop()
                    self.keyboard_hook.key_released.disconnect()
                    self.keyboard_hook = None
                    self._log_with_time("[로그] 키보드 모니터링 중지")
                except Exception as e:
                    self._log_with_time("[오류] 키보드 모니터링 중지 실패: {}".format(str(e)))
    
    def _safe_cleanup(self):
        """안전한 정리 작업"""
        self._log_with_time("[로그] 안전한 정리 작업 시작")
        try:
            # 먼저 실행 상태를 False로 설정
            self._log_with_time("[로그] 실행 상태 False로 설정 시작")
            self._update_state(is_executing=False)
            self._log_with_time("[로그] 실행 상태 False로 설정 완료")

            # 중지 상태를 False로 설정
            self._log_with_time("[로그] 중지 상태 False로 설정 시작")
            self._update_state(is_stopping=False)
            self._log_with_time("[로그] 중지 상태 False로 설정 완료")

            # 현재 단계와 반복 횟수 초기화
            self._log_with_time("[로그] 단계와 반복 횟수 초기화 시작")
            self._update_state(current_step=0, current_repeat=1)
            self._log_with_time("[로그] 단계와 반복 횟수 초기화 완료")

            self._log_with_time("[로그] 안전한 정리 작업 완료")
            self.cleanup_finished.emit()
            self._log_with_time("[로그] 정리 완료 시그널 발생")
        except Exception as e:
            self._log_with_time("[오류] 안전한 정리 작업 중 오류 발생: {}".format(str(e)))
            self.execution_error.emit("정리 작업 중 오류 발생: {}".format(str(e)))
    
    def _on_key_released(self, key_info):
        """키를 뗄 때 호출
        
        Args:
            key_info (dict): 입력된 키 정보
        """
        self._log_with_time("[로그] 키 입력 감지: {}".format(key_info))
        
        # ESC 키 감지 (virtual_key = 27)
        if key_info.get('virtual_key') == 27:
            self._log_with_time("[로그] ESC 키 감지 - 로직 강제 중지 실행")
            self.force_stop()
            return
        
        if not self._should_execute_logic():
            self._log_with_time("[로그] 로직 실행 조건이 맞지 않습니다.")
            return
            
        # 로직 찾기 및 실행
        for logic_name, logic in self.logic_manager.get_all_logics().items():
            if self._is_trigger_key_matched(logic, key_info):
                if self.execution_state['is_executing']:
                    self._log_with_time("[로그] 현재 다른 로직이 실행 중이므로 '{}' 로직을 실행할 수 없습니다.".format(logic_name))
                    return
                    
                try:
                    self.selected_logic = logic
                    self._update_state(
                        is_executing=True,
                        current_step=0,
                        current_repeat=1
                    )
                    # 로직 실행 시작 시 시간 초기화
                    self._start_time = time.time()
                    self._log_with_time("[로그] 로직 '{}' 실행 시작".format(logic_name))
                    
                    self.execution_started.emit()
                    
                    # 비동기적으로 첫 번째 스텝 실행
                    QTimer.singleShot(0, self._execute_next_step)
                    return
                    
                except Exception as e:
                    self._log_with_time("[오류] 로직 시작 중 오류 발생: {}".format(str(e)))
                    self._safe_cleanup()
                    
        self._log_with_time("[로그] 일치하는 트리거 키를 찾을 수 없습니다.")
    
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
                
                self._log_with_time("[로그] 현재 {}/{} 반복 완료".format(current_repeat, repeat_count))
                
                if current_repeat < repeat_count:
                    # 아직 반복 횟수 남았으면 처음부터 다시 시작
                    self._update_state(
                        current_step=0,
                        current_repeat=current_repeat + 1
                    )
                    QTimer.singleShot(0, self._execute_next_step)
                else:
                    # 현재 로직 완료
                    self._log_with_time("[로그] 로직 '{}' 실행 완료".format(self.selected_logic.get('name')))
                    
                    # 스택에 이전 로직이 있으면 복원
                    if self._logic_stack:
                        prev_logic, prev_state = self._logic_stack.pop()
                        self.selected_logic = prev_logic
                        self._update_state(**prev_state)
                        QTimer.singleShot(0, self._execute_next_step)
                    else:
                        # 모든 로직 실행 완료
                        self._safe_cleanup()
                        self.execution_finished.emit()
                return
                
            # 현재 스텝 실행
            step = items[current_step]
            self._update_state(current_step=current_step + 1)
            self._execute_step(step)
            
        except Exception as e:
            self._log_with_time("[오류] 다음 스텝 실행 중 오류 발생: {}".format(str(e)))
            self._safe_cleanup()
    
    def _execute_step(self, step):
        """실제로 해당 스텝이 가지고 있는 어떤 동작을 수행하는 작업자 함수"""
        if self.execution_state['is_stopping']:
            return
            
        try:
            self._log_with_time("[로그] 스텝 {} 실행: {}".format(self.execution_state['current_step'], step['display_text']))
            
            if step['type'] == 'key_input':
                self._execute_key_input(step)
                # 키 입력 후 지연
                timer = QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(lambda: self._schedule_next_step())
                timer.start(int(self.KEY_INPUT_DELAY * 1000))
                self._active_timers.append(timer)
            elif step['type'] == 'delay':
                duration = float(step['duration'])
                self._log_with_time("[로그] {}초 대기 시작".format(duration))
                timer = QTimer()
                timer.setSingleShot(True)
                timer.timeout.connect(lambda: self._schedule_next_step())
                timer.start(int(duration * 1000))
                self._active_timers.append(timer)
            elif step['type'] == 'logic':
                self._execute_nested_logic(step)
                # 중첩 로직은 자체적으로 다음 스텝을 예약
                
        except Exception as e:
            self._log_with_time("[오류] 스텝 실행 중 오류 발생: {}".format(str(e)))
            self._safe_cleanup()

    def _schedule_next_step(self):
        """다음 스텝 실행을 예약"""
        if not self.execution_state['is_stopping']:
            QTimer.singleShot(0, self._execute_next_step)
    
    def _execute_key_input(self, step):
        """키 입력 실행"""
        try:
            virtual_key = step['virtual_key']
            scan_code = step['scan_code']
            flags = 0
            
            # 확장 키 플래그 설정
            if step['key_code'] == '숫자패드 엔터' or scan_code > 0xFF:
                flags |= win32con.KEYEVENTF_EXTENDEDKEY
            
            # 쉼표 키 특별 처리
            if step['key_code'] == ',':
                virtual_key = win32api.VkKeyScan(',') & 0xFF
                
            self._log_with_time("[로그] 키 입력 시도 - 키: {}, 가상키: {}, 스캔코드: {}, 플래그: {}".format(step['key_code'], virtual_key, scan_code, flags))
            
            if step['action'] == '누르기':
                win32api.keybd_event(virtual_key, scan_code, flags, 0)
            else:  # 떼기
                win32api.keybd_event(virtual_key, scan_code, flags | win32con.KEYEVENTF_KEYUP, 0)
                
        except Exception as e:
            raise Exception("키 입력 실행 실패: {}".format(str(e)))

    def _execute_nested_logic(self, step):
        """중첩 로직 실행"""
        logic_id = step.get('logic_id')
        if not logic_id:
            self._log_with_time("[로그] 로직 ID가 지정되지 않았습니다.")
            return

        nested_logic = self.logic_manager.get_all_logics().get(logic_id)
        if not nested_logic:
            self._log_with_time("[로그] 로직 ID '{}'를 찾을 수 없습니다.".format(logic_id))
            return

        # 중첩 로직 순환 참조 검사
        if any(logic.get('id') == logic_id for logic, _ in self._logic_stack):
            self._log_with_time("[로그] 로직 ID '{}'가 이미 실행 중입니다. 중첩 실행을 방지합니다.".format(logic_id))
            self.execution_error.emit("로직 ID '{}'의 중첩 실행이 감지되었습니다.".format(logic_id))
            return

        # 현재 실행 상태 저장
        current_state = {
            'current_step': self.execution_state['current_step'],
            'current_repeat': self.execution_state['current_repeat'],
            'is_stopping': self.execution_state['is_stopping']
        }
        self._logic_stack.append((self.selected_logic, current_state))

        # 중첩 로직 설정
        nested_logic = dict(nested_logic)
        self.selected_logic = nested_logic

        # 새로운 상태로 시작
        self._update_state(
            current_step=0,
            current_repeat=1,
            is_executing=True,
            is_stopping=False
        )

        self._log_with_time("[로그] 중첩 로직 '{}' 실행 시작 (총 {}회 반복)".format(nested_logic.get('name'), nested_logic.get('repeat_count', 1)))
        
        # 중첩 로직의 첫 스텝을 비동기적으로 실행
        QTimer.singleShot(0, self._execute_next_step)

    def stop_all_logic(self):
        """모든 실행 중인 로직을 강제로 중지"""
        self._log_with_time("[로그] 모든 로직 강제 중지 시작")
        
        with self._cleanup_lock:
            try:
                # 모든 활성 타이머 중지
                self._log_with_time("[로그] 활성 타이머 개수: {}".format(len(self._active_timers)))
                for timer in self._active_timers:
                    try:
                        timer.stop()
                        timer.deleteLater()
                        self._log_with_time("[로그] 타이머 중지 성공")
                    except Exception as e:
                        self._log_with_time("[오류] 타이머 중지 실패: {}".format(str(e)))
                self._active_timers.clear()
                self._log_with_time("[로그] 모든 타이머 중지 완료")
                
                # 현재 실행 중인 로직의 키만 해제
                if self.selected_logic and 'items' in self.selected_logic:
                    self._log_with_time("[로그] 선택된 로직: {}".format(self.selected_logic.get('name')))
                    pressed_keys = set()
                    for item in self.selected_logic['items']:
                        if item.get('type') == 'key_input' and item.get('action') == '누르기':
                            vk = item.get('virtual_key')
                            if vk:
                                pressed_keys.add(vk)
                    
                    self._log_with_time("[로그] 해제할 키 개수: {}".format(len(pressed_keys)))
                    # 누르기 상태인 키들만 해제
                    for vk in pressed_keys:
                        try:
                            win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                            self._log_with_time("[로그] 키 해제 성공: {}".format(vk))
                        except Exception as e:
                            self._log_with_time("[오류] 키 해제 실패 (VK: {}): {}".format(vk, str(e)))
                else:
                    self._log_with_time("[로그] 해제할 키가 없음")
                
                # 키보드 훅 정리
                with self._hook_lock:
                    if self.keyboard_hook:
                        self._log_with_time("[로그] 키보드 훅 정리 시작")
                        try:
                            self.keyboard_hook.stop()
                            self.keyboard_hook.key_released.disconnect()
                            self.keyboard_hook = None
                            self._log_with_time("[로그] 키보드 훅 정리 성공")
                        except Exception as e:
                            self._log_with_time("[오류] 키보드 훅 정리 실패: {}".format(str(e)))
                    else:
                        self._log_with_time("[로그] 키보드 훅이 없음")
                
                # 실행 상태 완전 초기화
                self.reset_execution_state()
                
                self._log_with_time("[로그] 모든 로직 강제 중지 완료")
                
            except Exception as e:
                self._log_with_time("[오류] 로직 중지 중 오류 발생: {}".format(str(e)))

    def force_stop(self):
        """강제 중지"""
        self._log_with_time("[로그] 강제 중지 함수 시작")
        
        try:
            # 먼저 stopping 상태로 설정
            self._update_state(is_stopping=True)
            
            # 모든 로직 중지 (이 함수 내에서 reset_execution_state()도 호출됨)
            self.stop_all_logic()
            
            # 키 입력 모니터링 다시 시작
            if self.is_logic_enabled:
                self.start_monitoring()
                self._log_with_time("[로그] 키 입력 모니터링 다시 시작")
            
            self._log_with_time("[로그] 강제 중지 완료")
            
        except Exception as e:
            self._log_with_time(f"[오류] 강제 중지 중 오류 발생: {str(e)}")

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
            self._log_with_time("[로그] 선택된 프로세스가 없습니다.")
            return False
            
        if not active_process:
            self._log_with_time("[로그] 활성 프로세스를 가져올 수 없습니다.")
            return False
            
        is_match = selected_process['pid'] == active_process['pid']
        return is_match

    def _is_trigger_key_matched(self, logic, key_info):
        """트리거 키 매칭 확인"""
        trigger_key = logic.get('trigger_key', {})
        self._log_with_time("[로그] 트리거 키 매칭 확인 - 트리거 키: {}, 입력 키: {}".format(trigger_key, key_info))
        
        # 가상 키와 스캔 코드만 비교
        return (trigger_key.get('virtual_key') == key_info.get('virtual_key') and
                trigger_key.get('scan_code') == key_info.get('scan_code'))

    def _log_with_time(self, message):
        """시간 정보가 포함된 로그 메시지 출력"""
        # 로직 실행과 관련된 로그인 경우에만 시간 정보 추가
        if any(keyword in message for keyword in [
            "스텝", "로직", "대기", "키 입력", "타이머",
            "상태 업데이트", "정리 작업"
        ]):
            elapsed = int((time.time() - self._start_time) * 1000)  # 밀리초 단위
            formatted_message = f"[{elapsed}ms] {message}"
        else:
            formatted_message = message
            
        self.log_message.emit(formatted_message)

    # 로직 실행 상태를 완전히 초기화하는 메서드 추가
    def reset_execution_state(self):
        """실행 상태를 완전히 초기화"""
        with self._state_lock:
            # execution_state 초기화
            self.execution_state = {
                'is_executing': False,
                'is_stopping': False,
                'current_step': 0,
                'current_repeat': 1
            }
            # 로직 스택 초기화
            self._logic_stack.clear()
            # 선택된 로직 초기화
            self.selected_logic = None
            # 시작 시간 초기화
            self._start_time = time.time()
            
            self.execution_state_changed.emit(self.execution_state.copy())

    def _clear_all_timers(self):
        """모든 타이머를 정리하는 메서드"""
        active_timers = len(self._active_timers)
        logger.info(f"활성 타이머 개수: {active_timers}")
        
        for timer in self._active_timers:
            try:
                timer.stop()
                timer.deleteLater()
            except:
                pass
                
        self._active_timers.clear()
        logger.info("모든 타이머 정리 완료")
