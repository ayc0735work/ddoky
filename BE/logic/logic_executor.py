import time
import win32api
import win32con
import win32gui
from PySide6.QtCore import QObject, Signal, QTimer
from ..utils.key_handler import KeyboardHook
from ..utils.mouse_handler import MouseHandler
import threading
from ..settings.settings import Settings

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
        
        # 설정에서 딜레이 값 로드
        settings = Settings()
        DEFAULT_DELAY = 0.0205
        
        # 기본 딜레이 값 설정
        default_delays = {
            'press': DEFAULT_DELAY,
            'release': DEFAULT_DELAY,
            'mouse_input': DEFAULT_DELAY,
            'default': DEFAULT_DELAY
        }
        
        # 키 딜레이 설정 로드
        saved_delays = settings.get('key_delays', {})
        
        # 설정에서 값을 가져오되, 없으면 기본값 사용
        delays = default_delays.copy()
        if isinstance(saved_delays, dict):
            for key in default_delays:
                if key in saved_delays:
                    delays[key] = saved_delays[key]
        
        self.KEY_DELAYS = {
            '누르기': delays['press'],
            '떼기': delays['release'],
            '마우스 입력': delays['mouse_input'],
            '기본': delays['default']
        }
        
        # 새로운 설정을 저장
        settings.set('key_delays', delays)
        
        # 리소스 관리
        self.keyboard_hook = None
        self.selected_logic = None
        
        # 동기화를 위한 락
        self._hook_lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._cleanup_lock = threading.Lock()
        
        # 로직 스택 (중첩로직 처리용)
        self._logic_stack = []
        
        # 시작 시간 저장
        self._start_time = 0
        
        # 활성 타이머 추적
        self._active_timers = []
        
        # 강제 중지 키 설정
        self.force_stop_key = 27  # 기본값으로 ESC 키 설정

    def _update_state(self, **kwargs):
        """상태 업데이트 및 알림"""
        self._log_with_time("[상태 로그] 상태 업데이트 시작: {}".format(kwargs))
        with self._state_lock:
            self._log_with_time("[상태 로그] 상태 락 획득")
            self.execution_state.update(kwargs)
            self.execution_state_changed.emit(self.execution_state.copy())
            self._log_with_time("[상태 로그] 상태 변경 알림 완료")
    
    def start_monitoring(self):
        """트리거 키 모니터링 작"""
        with self._hook_lock:
            if self.execution_state['is_executing'] or self.keyboard_hook:
                return
                
            try:
                self.keyboard_hook = KeyboardHook()
                self.keyboard_hook.key_released.connect(self._on_key_released)
                self.keyboard_hook.start()
                self._log_with_time("[중지 로그] 키보드 모니터링 시작")
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
                    self._log_with_time("[중지 로그] 키보드 모니터링 중지")
                except Exception as e:
                    self._log_with_time("[오류] 키보드 모니터링 중지 실패: {}".format(str(e)))
    
    def _safe_cleanup(self):
        """안전한 정리 작업"""
        self._log_with_time("[마무리 로그] 안전한 정리 작업 시작")
        try:
            # 먼저 실행 상태를 False로 설정
            self._log_with_time("[마무리 로그] 실행 상태 False로 설정 시작")
            self._update_state(is_executing=False)
            self._log_with_time("[마무리 로그] 실행 상태 False로 설정 완료")

            # 중지 상태를 False로 설정
            self._log_with_time("[마무리 로그] 중지 상태 False로 설정 시작")
            self._update_state(is_stopping=False)
            self._log_with_time("[마무리 로그] 중지 상태 False로 설정 완료")

            # 현재 단계와 반복 횟수 초기화
            self._log_with_time("[마무리 로그] 단계와 반복 횟수 초기화 시작")
            self._update_state(current_step=0, current_repeat=1)
            self._log_with_time("[마무리 로그] 단계와 반복 횟수 초기화 완료")

            self._log_with_time("[마무리 로그] 안전한 정리 작업 완료")
            self.cleanup_finished.emit()
            self._log_with_time("[마무리 로그] 정리 완료 시그널 발생")
        except Exception as e:
            self._log_with_time("[오류] 안전한 정리 작업 중 오류 발생: {}".format(str(e)))
            self.execution_error.emit("정리 작업 중 오류 발생: {}".format(str(e)))
    
    def set_force_stop_key(self, virtual_key):
        """강제 중지 키 설정
        
        Args:
            virtual_key (int): 설정할 가상 키 코드
        """
        self.force_stop_key = virtual_key
        self._log_with_time(f"[설정] 강제 중지 키가 변경되었습니다 (가상 키 코드: {virtual_key})")

    def _on_key_released(self, key_info):
        """키를 뗄 때 호출
        
        Args:
            key_info (dict): 입력된 키 정보
        """
        self._log_with_time("[키 감지 로그] 키 입력 감지: {}".format(key_info))
        
        # 강제 중지 키 감지
        if key_info.get('virtual_key') == self.force_stop_key:
            self._log_with_time("[키 감지 로그] 강제 중지 키 감지 - 로직 강제 중지 실행")
            self.force_stop()
            return
        
        if not self._should_execute_logic():
            self._log_with_time("[로그] 로직 실행 조건이 맞지 않습니다.")
            return
            
        # 최신 로직 정보로 로직 찾기 및 실행
        found_matching_logic = False
        logics = self.logic_manager.get_all_logics(force=True)
        
        for logic_id, logic in logics.items():
            if self._is_trigger_key_matched(logic, key_info):
                found_matching_logic = True
                if self.execution_state['is_executing']:
                    self._log_with_time("다른 로직이 실행 중입니다.")
                    return
                    
                try:
                    self.selected_logic = logic
                    self.selected_logic['id'] = logic_id  # ID 정보 추가
                    self._update_state(
                        is_executing=True,
                        current_step=0,
                        current_repeat=1
                    )
                    # 로직 실행 시작 시간 초기화
                    # self._start_time = time.time()
                    self._log_with_time(f"[로직 실행] 로직 '{logic.get('name')}({logic_id})' 실행 시작")
                    
                    self.execution_started.emit()
                    
                    # 비동기적으로 첫 번째 스텝 실행
                    QTimer.singleShot(0, self._execute_next_step)
                    return
                    
                except Exception as e:
                    self._log_with_time("[오류] 로직 시작 중 오류 발생: {}".format(str(e)))
                    self._safe_cleanup()
                    
        if not found_matching_logic:
            self._log_with_time("[로그] 일치하는 트리거 키를 찾을 수 없습니다.")
    
    def _execute_next_step(self):
        """현재 실행할 스텝이 무엇인지 결정하는 관련자 함수"""
        if not self.selected_logic or self.execution_state['is_stopping']:
            return
            
        try:
            items = self.selected_logic.get('items', [])
            current_step = self.execution_state['current_step']
            
            # 모든 스텝이 완료되었는지 확인
            if current_step >= len(items):
                repeat_count = self.selected_logic.get('repeat_count', 1)
                current_repeat = self.execution_state['current_repeat']
                
                # 현재 실행 중인 로직 정보
                current_logic_name = self.selected_logic.get('name', '')
                current_logic_id = self.selected_logic.get('id', '')
                
                # 부모 로직이 있는 경우 (중첩로직인 경우)
                if self._logic_stack:
                    parent_logic, parent_state = self._logic_stack[-1]
                    parent_name = parent_logic.get('name', '')
                    parent_id = parent_logic.get('id', '')
                    parent_step = parent_state.get('current_step', 0)
                    parent_info = f" - {parent_name}({parent_id})의 {parent_step}번 스텝"
                    self._log_with_time(f"[로직-중첩로직]{parent_info} 중첩로직 '{current_logic_name}({current_logic_id})' {current_repeat}/{repeat_count} 반복 완료")
                else:
                    # 일반 로직의 경우
                    self._log_with_time(f"[로직 실행] 로직 '{current_logic_name}({current_logic_id})' {current_repeat}/{repeat_count} 반복 완료")
                
                if current_repeat < repeat_count:
                    # 아직 반복 횟수 남았으면 처음부터 다시 시작
                    self._update_state(
                        current_step=0,  # 스텝을 0으로 초기화
                        current_repeat=current_repeat + 1  # 반복 횟수 증가
                    )
                    # 다음 반복 실행을 위해 비동기 호출
                    QTimer.singleShot(0, self._execute_next_step)
                else:
                    # 모든 반복이 완료된 경우
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
            self._log_with_time(f"[오류] 다음 스텝 실행 중 오류 발생: {str(e)}")
            self._safe_cleanup()
    
    def _execute_step(self, step):
        """실제로 해당 스텝이 가지고 있는 어떤 동작을 수행하는 작업자 함수"""
        try:
            step_type = step.get('type')
            
            if step_type == 'key_input':
                self._execute_key_input(step)
            elif step_type == 'delay':
                self._execute_delay(step)
            elif step_type == 'logic':
                self._execute_nested_logic(step)
            elif step_type == 'mouse_input':
                self._execute_mouse_input(step)
            else:
                self._log_with_time(f"[오류] 알 수 없는 스텝 타입: {step_type}")
                
            # 다음 스텝 실행을 위해 비동기 호출
            QTimer.singleShot(0, self._execute_next_step)
            
        except Exception as e:
            self._log_with_time(f"[오류] 스텝 실행 중 오류 발생: {str(e)}")
            self._safe_cleanup()
    
    def _execute_key_input(self, step):
        """키 입력 실행"""
        try:
            # 키 입력 관련 정보 미리 계산
            virtual_key = step['virtual_key']
            scan_code = step['scan_code']
            flags = 0
            
            # 확장 키 플래그 설정
            if step['key_code'] == '숫자패드 엔터' or scan_code > 0xFF:
                flags |= win32con.KEYEVENTF_EXTENDEDKEY
            
            # 쉼표 키 특별 처리
            if step['key_code'] == ',':
                virtual_key = win32api.VkKeyScan(',') & 0xFF
                
            # 키 입력 실행
            if step['action'] == '누르기':
                win32api.keybd_event(virtual_key, scan_code, flags, 0)
            else:  # 떼기
                win32api.keybd_event(virtual_key, scan_code, flags | win32con.KEYEVENTF_KEYUP, 0)
                
            # 키 입력 후 지연
            time.sleep(self.KEY_DELAYS.get(step['action'], self.KEY_DELAYS['기본']))
            
            self._log_with_time(f"[키 입력] {step['display_text']} 실행 완료")
            
        except Exception as e:
            self._log_with_time(f"[오류] 키 입력 실행 중 오류 발생: {str(e)}")
            raise

    def _execute_delay(self, step):
        """지연시간 실행"""
        try:
            duration = float(step['duration'])
            time.sleep(duration)
            self._log_with_time(f"[지연시간] {duration}초 대기 완료")
        except Exception as e:
            self._log_with_time(f"[오류] 지연시간 실행 중 오류 발생: {str(e)}")
            raise

    def _execute_nested_logic(self, step):
        """중첩로직 실행"""
        try:
            logic_id = step.get('logic_id')
            if not logic_id:
                raise Exception("중첩로직의 ID가 없습니다.")
            
            # 현재 상태를 스택에 저장
            self._logic_stack.append((
                self.selected_logic,
                {
                    'current_step': self.execution_state['current_step'],
                    'current_repeat': self.execution_state['current_repeat']
                }
            ))
            
            # 최신 로직 정보로 중첩로직 로드 및 실행
            logics = self.logic_manager.get_all_logics(force=True)
            nested_logic = logics.get(logic_id)
            if not nested_logic:
                raise Exception(f"중첩로직을 찾을 수 없습니다: {logic_id}")
            
            nested_logic['id'] = logic_id  # ID 정보 추가
            self.selected_logic = nested_logic
            self._update_state(
                current_step=0,
                current_repeat=1
            )
            
            self._log_with_time(f"[중첩로직] {nested_logic.get('name')} 실행 시작")
            
        except Exception as e:
            self._log_with_time(f"[오류] 중첩로직 실행 중 오류 발생: {str(e)}")
            raise

    def _execute_mouse_input(self, step):
        """마우스 입력 실행"""
        try:
            # 현재 선택된 프로세스의 핸들 가져오기
            process = self.process_manager.get_selected_process()
            if not process or not process.get('hwnd'):
                self._log_with_time("[마우스 입력 상세] 선택된 프로세스가 없음")
                raise Exception("선택된 프로세스가 없습니다.")

            hwnd = process['hwnd']
            
            # DPI 스케일링 고려
            try:
                dpi = win32gui.GetDpiForWindow(hwnd)
                scale_factor = dpi / 96.0  # 기본 DPI는 96
            except AttributeError:
                scale_factor = 1.0
            
            # 클라이언트 영역의 크기와 화면상 시작점 가져오기
            client_rect = win32gui.GetClientRect(hwnd)
            client_width = int(client_rect[2] * scale_factor)
            client_height = int(client_rect[3] * scale_factor)
            client_point = win32gui.ClientToScreen(hwnd, (0, 0))
            
            # 저장된 비율 가져오기
            x_ratio = step.get('ratios_x', 0)
            y_ratio = step.get('ratios_y', 0)
            
            # 클라이언트 영역 크기를 기준으로 상대 좌표 계산
            client_x = int(client_width * x_ratio)
            client_y = int(client_height * y_ratio)
            
            # 클라이언트 영역의 화면상 좌표 계산
            screen_x = client_point[0] + client_x
            screen_y = client_point[1] + client_y
            
            self._log_with_time(f"[마우스 입력 상세] DPI 배율 - {scale_factor:.2f}")
            self._log_with_time(f"[마우스 입력 상세] 클라이언트 크기 - 너비: {client_width}, 높이: {client_height}")
            self._log_with_time(f"[마우스 입력 상세] 클라이언트 시작점 - X: {client_point[0]}, Y: {client_point[1]}")
            self._log_with_time(f"[마우스 입력 상세] 저장된 비율 - X: {x_ratio:.3f}, Y: {y_ratio:.3f}")
            self._log_with_time(f"[마우스 입력 상세] 클라이언트 내 좌표 - X: {client_x}, Y: {client_y}")
            self._log_with_time(f"[마우스 입력 상세] 화면 좌표 - X: {screen_x}, Y: {screen_y}")
            
            # 클릭 실행
            success = MouseHandler.click(screen_x, screen_y)
            if not success:
                self._log_with_time("[마우스 입력 상세] 마우스 클릭 실행 실패")
                raise Exception("마우스 클릭 실행 실패")
            
            self._log_with_time(f"[마우스 입력] {step.get('name')} 실행 완료")
            
        except Exception as e:
            self._log_with_time(f"[오류] 마우스 입력 실행 중 오류 발생: {str(e)}")
            raise

    def stop_all_logic(self):
        """모든 실행 중인 로직을 강제로 중지"""
        self._log_with_time("[로그] 모든 로직 강제 중지 시작")
        
        with self._cleanup_lock:
            try:
                # 모저 실행 상태를 중지로 설정하여 새로운 타이머 생성 방지
                self._update_state(is_stopping=True)
                
                # 타이머 정리를 비동기적으로 처리
                self._clear_timers_async()
                
                # 키보드 입력 상태 정리
                self._clear_keyboard_state()
                
                # 실행 상태 초기화
                self.reset_execution_state()
                
            except Exception as e:
                self._log_with_time("[오류] 로직 중지 중 오류 발생: {}".format(str(e)))

    def _clear_timers_async(self):
        """타이머를 비동기적으로 정리"""
        self._log_with_time(f"[로그] 타이머 정리 시작 (총 {len(self._active_timers)}개)")
        
        # 타이머를 작은 그룹으로 나누어 처리
        BATCH_SIZE = 10
        timer_groups = [self._active_timers[i:i + BATCH_SIZE] 
                       for i in range(0, len(self._active_timers), BATCH_SIZE)]
        
        def clear_timer_group():
            if not timer_groups:
                self._active_timers.clear()
                self._log_with_time("[로그] 모든 타이머 정리 완료")
                return
            
            group = timer_groups.pop(0)
            for timer in group:
                try:
                    timer.stop()
                    timer.deleteLater()
                except:
                    pass
                
            # 다음 그룹을 처리하기 위해 새로운 타이머 생성
            QTimer.singleShot(0, clear_timer_group)
        
        # 첫 번째 그룹 처리 시작
        QTimer.singleShot(0, clear_timer_group)

    def _clear_keyboard_state(self):
        """키보드 상태 정"""
        if self.selected_logic and 'items' in self.selected_logic:
            pressed_keys = set()
            for item in self.selected_logic['items']:
                if item.get('type') == 'key_input' and item.get('action') == '누르기':
                    vk = item.get('virtual_key')
                    if vk:
                        pressed_keys.add(vk)
            
            self._log_with_time(f"[로그] 키 상태 정리 시작 (총 {len(pressed_keys)}개)")
            for vk in pressed_keys:
                try:
                    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                except Exception as e:
                    self._log_with_time(f"[오류] 키 해제 실패 (VK: {vk}): {str(e)}")

    def force_stop(self):
        """강제 중지"""
        self._log_with_time("[로그] 강제 중지 함수 시작")
        
        try:
            # 먼저 stopping 상태로 설정
            self._update_state(is_stopping=True)
            
            # 모든 로직 중지 (reset_execution_state()도 호출됨)
            self.stop_all_logic()
            
            # 키 입력 모니터링 다시 시작
            if self.is_logic_enabled:
                self.start_monitoring()
                self._log_with_time("[로그] 키 입력 니터링 다시 시작")
            
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
        # 중첩 로인 경우 매칭하지 않음
        if logic.get('is_nested', False):
            return False
        
        trigger_key = logic.get('trigger_key', {})
        self._log_with_time("[로그] 트리거 키 매칭 확인 - 트리거 키: {}, 입력 키: {}".format(trigger_key, key_info))
        
        # trigger_key나 key_info가 None인 경우 처리
        if not trigger_key or not key_info:
            return False
        
        # 가상 키와 스캔 코드만 비교
        return (trigger_key.get('virtual_key') == key_info.get('virtual_key') and
                trigger_key.get('scan_code') == key_info.get('scan_code'))

    def _log_with_time(self, message):
        """시간 정보가 포함된 로그 메시지 출력"""
        
        # 무시할 로그 메시지 패턴
        ignore_patterns = [
            "키 입력 도",
            "키 입력 감지",
            "로직 실행 조건이 맞지 않습니다",
            "상태 업데이트 작",
            "상태 락 획득",
            "새로운 상태",
            "상태 변경 알림 완료",
            "상태 업데이트 시작",
            "[상태 로그]"
        ]

        # 무시할 패턴이 포함된 메시지는 로깅하지 않음
        if any(pattern in message for pattern in ignore_patterns):
            return

        # 시간 정보를 포함할 로그 패턴
        time_patterns = [
            "로직 실행 시작",
            "로직 실행 완료",
            "중첩로직",
            "반복 완료",
            "강제 중지",
            "타이머 정리",
            "키 상태 정리",
            "스텝",
            "지연시간",
            "키 입력"
        ]

        # 시간 정보 포함 패턴이 있는 경우 시간 정보 추가
        if any(pattern in message for pattern in time_patterns):
            elapsed = time.time() - self._start_time
            time_info = f"[{elapsed:.4f}초]"
        else:
            time_info = ""

        # 메시지 스타일 적용
        if "[오류]" in message:
            # 오류 메시지 - 어두운 빨간색
            formatted_message = f"<span style='color: #FFA500; font-size: 14px;'>{time_info}</span> <span style='color: #FFA500; font-size: 12px;'>{message}</span>"
        
        elif "ESC 키 감지" in message or "강제 중지" in message:
            formatted_message = f"<span style='color: #FF0000; font-size: 24px; font-weight: bold;'>{time_info}</span> <span style='color: #FF0000; font-size: 18px; font-weight: bold;'>{message}</span>"
        
        elif "중첩로직" in message:
            formatted_message = f"<span style='color: #008000; font-size: 28px; font-weight: bold;'>{time_info}</span> <span style='color: #008000; font-size: 18px; font-weight: bold;'>{message}</span>"

        elif "키 입력: 숫자패드 9" in message or "키 입력: 숫자패드 8" in message:
            formatted_message = f"<span style='color: #FF00FF; font-size: 12px; font-weight: bold;'>{time_info}</span> <span style='color: #FF00FF; font-size: 12px; font-weight: bold;'>{message}</span>"

        elif "로직 실행" in message and ("실행 시작" in message or "반복 완료" in message):
            formatted_message = f"<span style='color: #0000FF; font-size: 34px; font-weight: bold;'>{time_info}</span> <span style='color: #0000FF; font-size: 24px; font-weight: bold;'>{message}</span>"
        else:
            # 기본 메시지 - 기본 스타일
            formatted_message = f"<span style='color: #000000;'>{time_info}</span> {message}"
            
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
            self._start_time = 0
            
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

    def save_logics_to_settings(self):
        """현재 로직 목록을 설정에 저장"""
        try:
            # 현재 설정을 다시 로드하여 최신 상태 유지
            self.settings_manager.reload_settings()
            
            # 로직 목록을 순회하면서 order 값 업데이트
            updated_logics = {}
            for i in range(self.SavedLogicList__QListWidget.count()):
                item = self.SavedLogicList__QListWidget.item(i)
                if item:
                    logic_id = item.data(Qt.UserRole)
                    if logic_id in self.settings_manager.settings.get('logics', {}):
                        logic_info = self.settings_manager.settings['logics'][logic_id]
                        
                        # 첫 번째 아이템의 order는 1로 설정하고, 나머지 2부터 순차적으로 증가
                        logic_info['order'] = 1 if i == 0 else i + 1
                        logic_info['updated_at'] = datetime.now().isoformat()
                        
                        # settings_manager를 통해 로직 저장 (필드 순서 정)
                        updated_logic = self.settings_manager.save_logic(logic_id, logic_info)
                        updated_logics[logic_id] = updated_logic
            
            # 모든 로직이 성공적으로 저장되면 saved_logics 업데이트
            self.saved_logics = updated_logics
            
            # settings_manager의 settings 업데이트 및 저장
            settings = self.settings_manager.settings.copy()
            settings['logics'] = updated_logics
            self.settings_manager._save_settings(settings)  # settings 인자 추가
            
            self.log_message.emit("로직이 성공적으로 저장되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"로직 저장 중 오류 발생: {str(e)}")
            # 오류 발생 시 저장된 로직 다시 불러기
            self.load_saved_logics()

    def execute_logic(self, logic_id, repeat_count=None):
        """로직을 실행"""
        try:
            # 실행 시점에 최신 로직 데이터 로드
            logics = self.settings_manager.load_logics(force=True)
            if logic_id not in logics:
                raise ValueError(f"로직을 찾을 수 없습니다: {logic_id}")
                
            logic_data = logics[logic_id]
            
            # repeat_count가 지정되지 않은 경우 로직의 기본값 사용
            if repeat_count is None:
                repeat_count = logic_data.get('repeat_count', 1)
                
            self.running = True
            self.stop_requested = False
            
            for _ in range(repeat_count):
                if self.stop_requested:
                    break
                    
                for item in logic_data.get('items', []):
                    if self.stop_requested:
                        break
                        
                    if item.get('type') == 'logic':
                        # 중첩로직 실행 시에도 최신 데이터 사용
                        nested_logic_id = item.get('logic_id')
                        if nested_logic_id:
                            nested_repeat = item.get('repeat_count', 1)
                            self.execute_logic(nested_logic_id, nested_repeat)
                    # ... 나머지 실행 로직 ...
                    
        except Exception as e:
            print(f"로직 실행 중 오류 발생: {str(e)}")
            raise
        finally:
            self.running = False
            self.stop_requested = False

    def _on_key_released(self, key_info):
        """키를 뗄 때 호출
        
        Args:
            key_info (dict): 입력된 키 정보
        """
        self._log_with_time("[키 감지 로그] 키 입력 감지: {}".format(key_info))
        
        # 강제 중지 키 감지
        if key_info.get('virtual_key') == self.force_stop_key:
            self._log_with_time("[키 감지 로그] 강제 중지 키 감지 - 로직 강제 중지 실행")
            self.force_stop()
            return
        
        if not self._should_execute_logic():
            self._log_with_time("[로그] 로직 실행 조건이 맞지 않습니다.")
            return
            
        # 최신 로직 정보로 로직 찾기 및 실행
        found_matching_logic = False
        logics = self.logic_manager.get_all_logics(force=True)
        
        for logic_id, logic in logics.items():
            if self._is_trigger_key_matched(logic, key_info):
                found_matching_logic = True
                if self.execution_state['is_executing']:
                    self._log_with_time("다른 로직이 실행 중입니다.")
                    return
                    
                try:
                    self.selected_logic = logic
                    self.selected_logic['id'] = logic_id  # ID 정보 추가
                    self._update_state(
                        is_executing=True,
                        current_step=0,
                        current_repeat=1
                    )
                    # 로직 실행 시작 시간 초기화
                    self._start_time = time.time()
                    self._log_with_time(f"[로직 실행] 로직 '{logic.get('name')}({logic_id})' 실행 시작")
                    
                    self.execution_started.emit()
                    
                    # 비동기적으로 첫 번째 스텝 실행
                    QTimer.singleShot(0, self._execute_next_step)
                    return
                    
                except Exception as e:
                    self._log_with_time("[오류] 로직 시작 중 오류 발생: {}".format(str(e)))
                    self._safe_cleanup()
                    
        if not found_matching_logic:
            self._log_with_time("[로그] 일치하는 트리거 키를 찾을 수 없습니다.")
