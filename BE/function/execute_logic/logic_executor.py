import time
import win32api
import win32con
import win32gui
from PySide6.QtCore import QObject, Signal, QTimer, Qt
from PySide6.QtWidgets import QApplication
from BE.function._common_components.modal.entered_key_info_modal.keyboard_hook_handler import KeyboardHook
from BE.function._common_components.mouse_handler import MouseHandler
import threading
from BE.settings.settings_data_manager import SettingsManager
import keyboard
from BE.log.manager.base_log_manager import BaseLogManager

class LogicExecutor(QObject):
    """로직 실행기"""
    
    # 기본 딜레이 값 (key_delays.json의 기본값)
    DEFAULT_DELAYS = {
        'press': 0.026,
        'release': 0.0017,
        'mouse_input': 0.0245,
        'default': 0.0025
    }
    
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
        self.modal_log_manager = BaseLogManager.instance()  # BaseLogManager 초기화
        
        # 로직 활성화 상태 추가
        self.is_logic_enabled = True
        
        # 키 입력 출처 플래그 추가
        self.is_step_input = False
        
        # 시뮬레이션된 키 입력 플래그 추가
        self.is_simulated_input = False
        
        # 상태 관리
        self.execution_state = {
            'is_executing': False,
            'is_stopping': False,
            'current_step': 0,
            'current_repeat': 1
        }
        
        # settings_manager 인스턴스 생성
        self.settings_manager = SettingsManager()
        
        # key_delays.json 파일에서 딜레이 값 로드
        delays = self.settings_manager.get('key_delays', self.DEFAULT_DELAYS)
        
        # KEY_DELAYS 설정
        self.KEY_DELAYS = {
            '누르기': delays['press'],
            '떼기': delays['release'],
            '마우스 입력': delays['mouse_input'],
            '기본': delays['default']
        }
        
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
        
        # 실행 중지 플래그 추가
        self._should_stop = False
        
        # ESC 키 시뮬레이션 시간 추적
        self.last_simulated_esc_time = 0

    def _update_state(self, **kwargs):
        """상태 업데이트 및 알림"""
        self.modal_log_manager.start_timer("상태업데이트모달")
        self.modal_log_manager.log(
            message=f"상태 업데이트 시작: {kwargs}",
            level="INFO",
            modal_name="상태업데이트모달",
            include_time=True
        )
        with self._state_lock:
            self.modal_log_manager.log(
                message="상태 락 획득",
                level="INFO", 
                modal_name="상태업데이트모달",
                include_time=True
            )
            self.execution_state.update(kwargs)
            self.execution_state_changed.emit(self.execution_state.copy())
            self.modal_log_manager.log(
                message="상태 변경 알림 완료",
                level="INFO",
                modal_name="상태업데이트모달",
                include_time=True
            )
        self.modal_log_manager.stop_timer("상태업데이트모달")
    
    def start_monitoring(self):
        """트리거 키 모니터링 시작"""
        with self._hook_lock:
            if self.execution_state['is_executing'] or self.keyboard_hook:
                return
                
            try:
                self.keyboard_hook = KeyboardHook()
                self.keyboard_hook.key_released.connect(self._on_key_released)
                self.keyboard_hook.start()
                self.modal_log_manager.log(
                    message="키보드 모니터링 시작",
                    level="INFO",
                    modal_name="모니터링모달",
                    include_time=True
                )
            except Exception as e:
                self.modal_log_manager.log(
                    message=f"키보드 모니터링 시작 실패: {str(e)}",
                    level="ERROR",
                    modal_name="모니터링모달"
                )
                self._safe_cleanup()
    
    def stop_monitoring(self):
        """트리거 키 모니터링 중지"""
        with self._hook_lock:
            if self.keyboard_hook:
                try:
                    self.keyboard_hook.stop()
                    self.keyboard_hook.key_released.disconnect()
                    self.keyboard_hook = None
                    self.modal_log_manager.log(
                        message="키보드 모니터링 중지",
                        level="INFO",
                        modal_name="모니터링모달",
                        include_time=True
                    )
                except Exception as e:
                    self.modal_log_manager.log(
                        message=f"키보드 모니터링 중지 실패: {str(e)}",
                        level="ERROR",
                        modal_name="모니터링모달"
                    )
    
    def _safe_cleanup(self):
        """안전한 정리 작업"""
        self.modal_log_manager.start_timer("정리모달")
        self.modal_log_manager.log(
            message="안전한 정리 작업 시작",
            level="INFO",
            modal_name="정리모달",
            include_time=True
        )
        try:
            # 먼저 실행 상태를 False로 설정
            self.modal_log_manager.log(
                message="실행 상태 False로 설정 시작",
                level="INFO",
                modal_name="정리모달",
                include_time=True
            )
            self._update_state(is_executing=False)
            self.modal_log_manager.log(
                message="실행 상태 False로 설정 완료",
                level="INFO",
                modal_name="정리모달",
                include_time=True
            )

            # 중지 상태를 False로 설정
            self.modal_log_manager.log(
                message="중지 상태 False로 설정 시작",
                level="INFO",
                modal_name="정리모달",
                include_time=True
            )
            self._update_state(is_stopping=False)
            self.modal_log_manager.log(
                message="중지 상태 False로 설정 완료",
                level="INFO",
                modal_name="정리모달",
                include_time=True
            )

            # 현재 단계와 반복 횟수 초기화
            self.modal_log_manager.log(
                message="단계와 반복 횟수 초기화 시작",
                level="INFO",
                modal_name="정리모달",
                include_time=True
            )
            self._update_state(current_step=0, current_repeat=1)
            self.modal_log_manager.log(
                message="단계와 반복 횟수 초기화 완료",
                level="INFO",
                modal_name="정리모달",
                include_time=True
            )

            self.modal_log_manager.log(
                message="안전한 정리 작업 완료",
                level="INFO",
                modal_name="정리모달",
                include_time=True
            )
            self.cleanup_finished.emit()
            self.modal_log_manager.log(
                message="정리 완료 시그널 발생",
                level="INFO",
                modal_name="정리모달",
                include_time=True
            )
        except Exception as e:
            self.modal_log_manager.log(
                message=f"정리 작업 중 오류 발생: {str(e)}",
                level="ERROR",
                modal_name="정리모달"
            )
            self.execution_error.emit(f"정리 작업 중 오류 발생: {str(e)}")
        self.modal_log_manager.stop_timer("정리모달")
    
    def set_force_stop_key(self, virtual_key):
        """강제 중지 키 설정
        
        Args:
            virtual_key (int): 설정할 가상 키 코드
        """
        self.force_stop_key = virtual_key
        self.modal_log_manager.log(
            message=f"강제 중지 키가 변경되었습니다 (가상 키 코드: {virtual_key})",
            level="INFO",
            modal_name="설정모달"
        )

    def _on_key_released(self, formatted_key_info):
        """키를 뗄 때 호출
        
        Args:
            formatted_key_info (dict): 입력된 키 정보
        """
        self.modal_log_manager.log(
            message=f"""
            키 이벤트 상세 정보
            - 입력된 키: {formatted_key_info}
            - 스텝 입력 여부: {self.is_step_input}
            - 시뮬레이션 여부: {self.is_simulated_input}
            """,
            level="DEBUG", 
            modal_name="키입력모달",
            print_to_terminal=True
        )

        self.modal_log_manager.log(
            message=f"키 입력이 감지되었습니다: {formatted_key_info.get('key_name', '알 수 없음')}",
            level="INFO",
            modal_name="키입력모달"
        )
        
        # 강제 중지 키(ESC) 처리 - 시뮬레이션된 입력이 아닐 때만 처리
        if not self.is_simulated_input and formatted_key_info.get('virtual_key') == self.force_stop_key:
            # 활성 프로세스와 선택된 프로세스가 동일한지 확인
            active_process = self.process_manager.get_active_process()
            selected_process = self.process_manager.get_selected_process()
            
            if active_process and selected_process and active_process['pid'] == selected_process['pid']:
                # 이미 중지 상태인지 확인
                if self._should_stop:
                    return
                    
                print("[DEBUG] 강이벤트 감지 종료 ----\n")
                self.modal_log_manager.log(
                    message="강제 중지 키 감지 - 로직 강제 중지 실행",
                    level="INFO",
                    modal_name="키입력모달",
                    include_time=True
                )
                self._should_stop = True
                self.force_stop()
            else:
                self.modal_log_manager.log(
                    message="강제 중지 키가 감지되었으나, 활성 프로세스가 선택된 프로세스와 다르므로 무시됩니다.",
                    level="WARNING",
                    modal_name="키입력모달"
                )
            return
            
        # 시뮬레이션된 입력 처리
        if self.is_simulated_input:
            self.modal_log_manager.log(
                message="시뮬레이션된 입력이 감지되어 무시됩니다",
                level="DEBUG",
                modal_name="키입력모달",
                print_to_terminal=True
            )
            return
        
        if not self._should_execute_logic():
            self.modal_log_manager.log(
                message="로직 실행 조건이 맞지 않습니다.",
                level="INFO",
                modal_name="로직실행모달"
            )
            return
            
        # 최신 로직 정보로 로직 찾기 및 실행
        found_matching_logic = False
        logics = self.logic_manager.get_all_logics(force=True)
        
        for logic_id, logic in logics.items():
            if self._is_trigger_key_matched(logic, formatted_key_info):
                found_matching_logic = True
                if self.execution_state['is_executing']:
                    self.modal_log_manager.log(
                        message="다른 로직이 실행 중입니다.",
                        level="WARNING",
                        modal_name="로직실행모달"
                    )
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
                    self.modal_log_manager.log(
                        message=(
                            f"<br>"
                            f"[로직 실행 시작] <br>"
                            f"- 로직 이름: {logic.get('name')} <br>"
                            f"- 로직 UUID: {logic_id}"
                        ),
                        level="INFO",
                        modal_name="로직실행모달",
                        include_time=True
                    )
                    
                    self.execution_started.emit()
                    
                    # 비동기적으로 첫 번째 스텝 실행
                    QTimer.singleShot(0, self._execute_next_step)
                    return
                    
                except Exception as e:
                    self.modal_log_manager.log(
                        message=f"로직 시작 중 오류 발생: {str(e)}",
                        level="ERROR",
                        modal_name="로직실행모달"
                    )
                    self._safe_cleanup()
                    
        if not found_matching_logic:
            self.modal_log_manager.log(
                message=f"일치하는 트리거 키를 찾을 수 없습니다.<br>입력된 키 정보: {formatted_key_info}<br>",
                level="WARNING",
                modal_name="키입력모달"
            )
    def _execute_next_step(self):
        """현재 실행할 스텝이 무엇인지 결정하는 관련자 함수"""
        if not self.selected_logic or self.execution_state['is_stopping']:
            return
            
        try:
            # order 필드를 기준으로 정렬된 아이템 목록을 가져옴
            items = sorted(self.selected_logic.get('items', []), key=lambda x: x.get('order', 0))
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
                    parentep = parent_state.get('current_step', 0)
                    
                    self.modal_log_manager.log(
                        message=(
                            f"[중첩로직 반복 완료] <br>"
                            f"- 반복횟수: {current_repeat}/{repeat_count} 반복 완료 <br>"
                            f"- 부모 로직: {parent_name} <br>"
                            f"- 중첩로직 이름: {current_logic_name} <br>"
                            f"- 중첩로직 UUID: {current_logic_id} <br>"
                        ),
                        level="INFO",
                        modal_name="로직실행",
                        include_time=True,
                    )
                else:
                    # 일반 로직의 경우
                    self.modal_log_manager.log(
                        message=(
                            f"[로직 실행] <br>"
                            f"- 반복횟수: {current_repeat}/{repeat_count} 반복 완료 <br>"
                            f"- 로직 이름: {current_logic_name} <br>"
                            f"- 로직 UUID: {current_logic_id} <br>"
                        ),
                        level="INFO",
                        modal_name="로직실행",
                        include_time=True,
                    )
                
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
            self._execute_item(step)
            
        except Exception as e:
            self.modal_log_manager.log(
                message=f"다음 스텝 실행 중 오류 발생: {str(e)}",
                level="ERROR",
                modal_name="로직실행",
                include_time=True
            )
            self._safe_cleanup()
    def _execute_item(self, item):
        """아이템 실행
        
        Args:
            item (dict): 실행할 아이템
        """
        try:
            if not self.is_logic_enabled:
                return
                
            # 아이템 타입에 따라 실행
            if item['type'] == 'key_input':
                self._execute_key_input(item)
            elif item['type'] == 'mouse_input':
                self._execute_mouse_input(item)
            elif item['type'] == 'delay':
                self._execute_delay(item)
            elif item['type'] == 'logic':
                self._execute_nested_logic(item)
            elif item['type'] == 'wait_click':
                self._execute_wait_click(item)
            elif item['type'] == 'write_text':
                self._execute_text_input(item)
            
            # 다음 스텝 실행을 위해 비동기 호출
            QTimer.singleShot(0, self._execute_next_step)
        except Exception as e:
            self.modal_log_manager.log(
                message=f"스텝 실행 중 오류가 발생했습니다: {str(e)}",
                level="ERROR",
                modal_name="로직실행",
                include_time=True
            )
            self._safe_cleanup()
    
    def _execute_key_input(self, step):
        """키 입력 실행"""
        try:
            self.is_step_input = True  # 스텝 입력 플래그 설정
            self.is_simulated_input = True  # 시뮬레이션 입력 플래그 설정
            self.modal_log_manager.log(
                message=f"""
                키 입력 실행 시작
                - 스텝 정보: {step}
                - 현재 스레드 ID: {threading.get_ident()}
                - 실행 시작 시간: {time.time()}
                - 플래그 상태:
                  * step_input: {self.is_step_input}
                  * simulated: {self.is_simulated_input}
                """,
                level="DEBUG",
                modal_name="로직실행",
                print_to_terminal=True
            )
            
            # ESC 키 입력인 경우 시간 기록
            if step['key_code'] == 'ESC':
                if step['action'] == '떼기':
                    self.last_simulated_esc_time = time.time()
                    self.modal_log_manager.log(
                        message=f"ESC 키 시뮬레이션 떼기 시간 기록: {self.last_simulated_esc_time}",
                        level="DEBUG",
                        modal_name="로직실행",
                        print_to_terminal=True
                    )
            
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
                self.modal_log_manager.log(
                    message=f"""
                    키 누르기 실행
                    - 가상 키: {virtual_key}
                    - 스캔 코드: {scan_code} 
                    - 플래그: {flags}
                    """,
                    level="DEBUG",
                    modal_name="로직실행",
                    print_to_terminal=True
                )
                win32api.keybd_event(virtual_key, scan_code, flags, 0)
            else:  # 떼기
                self.modal_log_manager.log(
                    message=f"""
                    키 떼기 실행
                    - 가상 키: {virtual_key}
                    - 스캔 코드: {scan_code}
                    - 플래그: {flags | win32con.KEYEVENTF_KEYUP}
                    """, 
                    level="DEBUG",
                    modal_name="로직실행",
                    print_to_terminal=True
                )
                win32api.keybd_event(virtual_key, scan_code, flags | win32con.KEYEVENTF_KEYUP, 0)
            
            self.modal_log_manager.log(
                message="win32api.keybd_event 호출 완료",
                level="DEBUG",
                modal_name="로직실행",
                print_to_terminal=True
            )
            
            # 키 입력 후 지연
            delay = self.KEY_DELAYS.get(step['action'], self.KEY_DELAYS['기본'])
            self.modal_log_manager.log(
                message=f"키 입력 후 대기 시작 (대기 시간: {delay}초)",
                level="DEBUG", 
                modal_name="로직실행",
                print_to_terminal=True
            )
            time.sleep(delay)
            self.modal_log_manager.log(
                message="키 입력 후 대기 완료",
                level="DEBUG",
                modal_name="로직실행", 
                print_to_terminal=True
            )
            
            # ESC 키를 떼는 경우 추가 딜레이
            if step['action'] == '떼기' and step['key_code'] == 'ESC':
                self.modal_log_manager.log(
                    message="ESC 키 떼기 후 추가 대기 시작 (대기 시간: 0.005초)",
                    level="DEBUG",
                    modal_name="로직실행",
                    print_to_terminal=True
                )
                time.sleep(0.005)
                self.modal_log_manager.log(
                    message="ESC 키 떼기 후 추가 대기 완료",
                    level="DEBUG", 
                    modal_name="로직실행",
                    print_to_terminal=True
                )
            self.modal_log_manager.log(
                message=f"키 입력 실행 완료: {step['display_text']}",
                level="INFO",
                modal_name="로직실행",
                include_time=True
            )
            
        finally:
            self.modal_log_manager.log(
                message=f"""
                키 입력 실행 종료
                - 종료 시간: {time.time()}
                - 스텝 입력 상태: {self.is_step_input}
                - 시뮬레이션 상태: {self.is_simulated_input}
                """,
                level="DEBUG",
                modal_name="로직실행",
                print_to_terminal=True
            )
            self.is_step_input = False  # 스텝 입력 플래그 해제
            self.is_simulated_input = False  # 시뮬레이션 입력 플래그 해제

    def _execute_delay(self, step):
        """지연시간 실행"""
        try:
            duration = float(step['duration'])
            time.sleep(duration)
            self.modal_log_manager.log(
                message=f"지연시간 {duration}초 대기 완료",
                level="INFO", 
                modal_name="로직실행",
                include_time=True
            )
        except Exception as e:
            self.modal_log_manager.log(
                message=f"지연시간 실행 중 오류 발생: {str(e)}",
                level="ERROR",
                modal_name="로직실행",
                print_to_terminal=True
            )
            raise

    def _execute_nested_logic(self, step):
        """중첩로직 실행"""
        try:
            logic_id = step.get('logic_id')
            logic_name = step.get('logic_name')
            if not logic_id:
                raise Exception("중첩로직의 ID가 없습니다.<br>")
            
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
                raise Exception(
                    f"""
                    <br>
                    중첩로직을 찾을 수 없습니다
                    - 중첩로직 이름: {logic_name} <br>
                    - 중첩로직 UUID: {logic_id} <br>
                    """
                    )
            
            nested_logic['id'] = logic_id  # ID 정보 추가
            self.selected_logic = nested_logic
            self._update_state(
                current_step=0,
                current_repeat=1
            )
            self.modal_log_manager.log(
                message=f"""
                [중첩로직 실행 시작] <br>
                - 중첩로직 이름: {nested_logic.get('name')} <br>
                - 중첩로직 UUID: {nested_logic.get('id')} <br>
                """,
                level="INFO",
                modal_name="로직실행",
                include_time=True,
                print_to_terminal=True
            )
            
        except Exception as e:
            self.modal_log_manager.log(
                message=f"중첩로직 실행 중 오류 발생: {str(e)}",
                level="ERROR", 
                modal_name="로직실행",
                include_time=True,
                print_to_terminal=True
            )
            raise

    def _execute_mouse_input(self, step):
        """마우스 입력 실행"""
        try:
            # 현재 선택된 프로세스의 핸들 가져오기
            process = self.process_manager.get_selected_process()
            if not process or not process.get('hwnd'):
                self.modal_log_manager.log(
                    message="선택된 프로세스가 없음",
                    level="DEBUG",
                    modal_name="로직실행",
                    include_time=True
                )
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
            
            # 마우스 입력 상세 정보 로깅
            self.modal_log_manager.log(
                message=f"""
                [마우스 입력 상세 정보] <br>
                - DPI 배율: {scale_factor:.2f} <br>
                - 클라이언트 크기: 너비 {client_width}, 높이 {client_height} <br>
                - 클라이언트 시작점: X {client_point[0]}, Y {client_point[1]} <br>
                - 저장된 비율: X {x_ratio:.3f}, Y {y_ratio:.3f} <br>
                - 클라이언트 내 좌표: X {client_x}, Y {client_y} <br>
                - 화면 좌표: X {screen_x}, Y {screen_y} <br>
                """,
                level="DEBUG",
                modal_name="로직실행",
                include_time=True
            )
            
            # 클릭 실행
            success = MouseHandler.click(screen_x, screen_y)
            if not success:
                self.modal_log_manager.log(
                    message="마우스 클릭 실행 실패",
                    level="ERROR",
                    modal_name="로직실행",
                    include_time=True,
                    print_to_terminal=True
                )
                raise Exception("마우스 클릭 실행 실패")
            
            self.modal_log_manager.log(
                message=f"마우스 입력 '{step.get('name')}' 실행 완료",
                level="INFO",
                modal_name="로직실행", 
                include_time=True
            )
            
        except Exception as e:
            self.modal_log_manager.log(
                message=f"마우스 입력 실행 중 오류 발생: {str(e)}",
                level="ERROR",
                modal_name="로직실행",
                include_time=True,
                print_to_terminal=True
            )
            raise

    def _execute_wait_click(self, item):
        """클릭 대기 실행
        
        이 메서드는 사용자가 마우스 왼쪽 버튼을 클릭할 때까지 대기합니다.
        QTimer를 사용하여 주기적으로 마우스 상태를 체크하며,
        이 과정에서 UI는 계속 반응하며 강제 중지(ESC)도 가능합니다.
        
        동작 과정:
        1. QTimer 생성 및 설정 (50ms 간격)
        2. 마우스 클릭 감지를 위한 check_click 함수 연결
        3. 타이머 시작 및 마우스 클릭 대기
        4. 클릭 감지 시 다음 단계로 진행
        
        Args:
            item (dict): 클릭 대기 아이템 정보를 담은 딕셔너리
        """
        # 시작 시간 기록
        start_time = self._start_time
        
        # 로그 출력으로 현재 상태 알림
        elapsed_time = time.time() - start_time
        self.modal_log_manager.log(
            message="마우스 왼쪽 버튼 클릭 또는 스페이스바 입력 -- 입력 대기 중...",
            level="INFO",
            modal_name="로직실행",
            include_time=True
        )
        
        # 마우스 버튼의 눌림/뗌 상태를 추적하기 위한 변수
        button_pressed = False
        
        # QTimer 객체 생성 및 설정
        # setSingleShot(False): 타이머가 반복적으로 실행되도록 설정
        # setInterval(5): 5밀리초(0.0005초) 간격으로 체크
        wait_timer = QTimer()
        wait_timer.setSingleShot(False)
        wait_timer.setInterval(5) # 5밀리초(0.0005초) 간격
        
        def check_click():
            """마우스 클릭 상태나 스페이스바 입력을 확인하는 콜백 함수
            
            매 타이머 간격(5ms)마다 실행되며:
            1. 강제 중지 여부 확인
            2. 마우스 왼쪽 버튼 상태 또는 스페이스바 입력 확인
            3. 버튼/키 상태 변화에 따른 처리
            """
            nonlocal button_pressed, start_time
            
            # 강제 중지 요청이 있는 경우 타이머 정리
            if self._should_stop:
                elapsed_time = time.time() - start_time
                self.modal_log_manager.log(
                    message="마우스 왼쪽 버튼 클릭 또는 스페이스바 입력 -- 강제 중지되었습니다",
                    level="INFO",
                    modal_name="로직실행",
                    include_time=True,
                    print_to_terminal=True
                )
                wait_timer.stop()
                wait_timer.deleteLater()
                return
                
            # win32api를 사용하여 마우스 왼쪽 버튼의 현재 상태 확인
            # GetAsyncKeyState 반환값에 0x8000 비트 마스크를 적용하여
            # 버튼이 눌렸는지 확인
            # 마우스 왼쪽 버튼과 스페이스바 상태 확인
            is_mouse_pressed = win32api.GetAsyncKeyState(win32con.VK_LBUTTON) & 0x8000
            is_space_pressed = win32api.GetAsyncKeyState(win32con.VK_SPACE) & 0x8000
            
            if (is_mouse_pressed or is_space_pressed) and not button_pressed:
                # 버튼이나 키가 처음 눌린 순간 감지
                button_pressed = True
                elapsed_time = time.time() - start_time
                input_type = "왼쪽 버튼" if is_mouse_pressed else "스페이스바"
                self.modal_log_manager.log(
                    message=f"마우스 왼쪽 버튼 클릭 또는 스페이스바 입력 -- {input_type}가 눌렸습니다",
                    level="INFO",
                    modal_name="로직실행",
                    include_time=True
                )
            elif not (is_mouse_pressed or is_space_pressed) and button_pressed:
                # 버튼이나 키가 떼진 순간 감지 및 다음 단계 진행
                elapsed_time = time.time() - start_time
                self.modal_log_manager.log(
                    message="마우스 왼쪽 버튼 클릭 또는 스페이스바 입력 -- 입력이 감지되어 다음 단계로 진행합니다",
                    level="INFO", 
                    modal_name="로직실행",
                    include_time=True,
                    print_to_terminal=True
                )
                wait_timer.stop()
                wait_timer.deleteLater()
        
        # 타이머에 체크 함수 연결 및 시작
        wait_timer.timeout.connect(check_click)
        self._active_timers.append(wait_timer)  # 메모리 관리를 위해 활성 타이머 목록에 추가
        wait_timer.start()
        
        # 타이머 완료 대기
        # processEvents()로 UI 반응성 유지하면서
        # 0.005초 간격으로 타이머 상태 확인
        while wait_timer.isActive() and not self._should_stop:
            QApplication.processEvents()  # UI 이벤트 처리 허용
            time.sleep(0.005)  # CPU 부하 감소를 위한 짧은 대기{{ ... }}

    def _clear_timers_async(self):
        """타이머를 비동기적으로 정리"""
        self.modal_log_manager.log(
            message=f"로직 강제 중지 -- 비동기로 실행된 타이머 정리를 시작합니다 (총 {len(self._active_timers)}개)",
            level="INFO",
            modal_name="로직실행",
            include_time=True,
            print_to_terminal=True
        )
        
        # 타이머를 작은 그룹으로 나누어 처리
        BATCH_SIZE = 10
        timer_groups = [self._active_timers[i:i + BATCH_SIZE] 
                       for i in range(0, len(self._active_timers), BATCH_SIZE)]
        
        def clear_timer_group():
            if not timer_groups:
                self._active_timers.clear()
                self.modal_log_manager.log(
                    message="로직 강제 중지 -- 비동기로 실행된 모든 타이머 정리가 완료되었습니다",
                    level="INFO",
                    modal_name="로직실행",
                    include_time=True,
                    print_to_terminal=True
                )
                # 모든 정리가 완료된 후 시간 초기화
                self._start_time = 0
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

    def _release_all_keys(self):
        """키보드 상태 정리 / 현재 눌려있는 모든 키를 떼는 함수"""
        pressed_keys = []
        # 모든 가상 키코드에 대해 검사 (0x01부터 0xFE까지)
        for vk in range(0x01, 0xFF):
            # 키가 눌려있는지 확인
            if win32api.GetAsyncKeyState(vk) & 0x8000:
                pressed_keys.append(vk)
                try:
                    # 키 떼기 이벤트 발생
                    win32api.keybd_event(vk, 0, win32con.KEYEVENTF_KEYUP, 0)
                except Exception as e:
                    self.modal_log_manager.log(
                        message=f"로직 강제 중지 -- 키 해제 실패 (가상 키: {vk}): {str(e)}",
                        level="ERROR",
                        modal_name="로직실행",
                        print_to_terminal=True
                    )
        
        self.modal_log_manager.log(
            message=f"로직 강제 중지 -- 키 상태 정리를 시작합니다 (총 {len(pressed_keys)}개의 키)",
            level="INFO",
            modal_name="로직실행",
            include_time=True
        )
        
        self.modal_log_manager.log(
            message="로직 강제 중지 -- 모든 키 떼기가 완료되었습니다",
            level="INFO", 
            modal_name="로직실행",
            include_time=True
        )

    def force_stop(self):
        """로직 강제 중지"""
        self.modal_log_manager.log(
            message="로직 강제 중지 -- 로직 강제 중지를 시작합니다",
            level="INFO",
            modal_name="로직실행",
            include_time=True,
            print_to_terminal=True
        )
        
        try:
            # 먼저 중지 상태로 설정
            self._update_state(is_stopping=True)
            
            # 키보드 상태 정리 - 모든 눌려있는 키 떼기
            self._release_all_keys()

            # 타이머 정리를 비동기적으로 처리
            self._clear_timers_async()

            # 실행 상태 초기화
            self.reset_execution_state()
            
            # 키 입력 모니터링 다시 시작
            if self.is_logic_enabled:
                self.start_monitoring()
            
            # ESC 키 두 번 누르기
            for _ in range(3):
                # 0.009초 딜레이
                time.sleep(0.009)
                # ESC 키 누르기
                win32api.keybd_event(27, 0, 0, 0)
                # ESC 키 떼기
                win32api.keybd_event(27, 0, win32con.KEYEVENTF_KEYUP, 0)
                # 0.009초 딜레이
                time.sleep(0.009)
                
            self.modal_log_manager.log(
                message="로직 강제 중지 -- ESC 키 세 번 눌렀다 떼기가 완료되었습니다",
                level="INFO",
                modal_name="로직실행",
                include_time=True
            )

            # 중지 상태 해제
            self._should_stop = False
            
            self.modal_log_manager.log(
                message="로직 강제 중지 -- 중지 상태가 해제되었습니다",
                level="INFO",
                modal_name="로직실행",
                include_time=True
            )

            self.modal_log_manager.log(
                message="로직 강제 중지 -- 로직 강제 중지가 완료되었습니다 <br>",
                level="INFO",
                modal_name="로직실행", 
                include_time=True,
                print_to_terminal=True
            )
            
        except Exception as e:
            self.modal_log_manager.log(
                message=f"로직 강제 중지 -- 강제 중지 중 오류가 발생했습니다: {str(e)}",
                level="ERROR",
                modal_name="로직실행",
                include_time=True,
                print_to_terminal=True
            )
    def _should_execute_logic(self):
        """로직 실행 조건 확인
        
        Returns:
            bool: 로직을 실행해야 하는지 여부
        """
        # 이미 실행 중이면 실행하지 않음
        if self.execution_state['is_executing']:
            self.modal_log_manager.log(
                message="로직이 이미 실행 중입니다",
                level="INFO",
                modal_name="로직실행"
            )
            return False
        
        # 선택된 프로세스와 활성 프로세스가 동일한지 확인
        selected_process = self.process_manager.get_selected_process()
        active_process = self.process_manager.get_active_process()
        
        if not selected_process:
            self.modal_log_manager.log(
                message="선택된 프로세스가 없습니다",
                level="WARNING",
                modal_name="로직실행"
            )
            return False
            
        if not active_process:
            self.modal_log_manager.log(
                message="활성 프로세스를 가져올 수 없습니다",
                level="WARNING", 
                modal_name="로직실행"
            )
            return False
            
        is_match = selected_process['pid'] == active_process['pid']
        return is_match

    def _is_trigger_key_matched(self, logic, formatted_key_info):
        """트리거 키 매칭 확인"""
        # 중첩 로직인 경우 매칭하지 않음
        if logic.get('is_nested', False):
            return False
        
        trigger_key = logic.get('trigger_key', {})
        
        # trigger_key나 formatted_key_info가 None인 경우 처리
        if not trigger_key or not formatted_key_info:
            return False
        
        # 가상 키와 스캔 코드 비교
        is_matched = (trigger_key.get('virtual_key') == formatted_key_info.get('virtual_key') and
                     trigger_key.get('scan_code') == formatted_key_info.get('scan_code'))
        
        # 매칭된 경우에만 로그 출력
        if is_matched:
            self.modal_log_manager.log(
                message=f"""
                트리거 키 매칭 확인
                - 트리거 키: {trigger_key}
                - 입력 키: {formatted_key_info}
                """,
                level="DEBUG",
                modal_name="로직실행",
                print_to_terminal=True
            )
        return is_matched

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
            "로직 강제 중지",
            "타이머 정리",
            "키 상태 정리",
            "스텝",
            "지연시간",
            "키 입력",
            "모든 키 떼기",
            "중지 상태",
            "마우스 왼쪽 버튼 클릭 또는 스페이스바 입력 대기"
        ]

        # 터미널 출력이 필요한 패턴
        terminal_patterns = [
            "로직 실행 시작",
            "로직 실행 완료",
            "중첩로직",
            "반복 완료",
            "로직 강제 중지",
            "오류"
        ]

        # 시간 정보 포함 여부 결정
        include_time = any(pattern in message for pattern in time_patterns)
        
        # 터미널 출력 여부 결정
        print_to_terminal = any(pattern in message for pattern in terminal_patterns)

        # 메시지 스타일 적용
        if "[오류]" in message:
            # 오류 메시지 - 어두운 빨간색
            formatted_message = f"<span style='color: #FFA500; font-size: 12px;'>{message}</span>"
        elif "로직 강제 중지" in message:
            formatted_message = f"<span style='color: #FF0000; font-size: 16px; font-weight: bold;'>{message}</span>"
        elif "중첩로직" in message:
            formatted_message = f"<span style='color: #008000; font-size: 18px; font-weight: bold;'>{message}</span>"
        elif "키 입력: 숫자패드 9" in message or "키 입력: 숫자패드 8" in message or "키 입력: 숫자패드 1" in message:
            formatted_message = f"<span style='color: #FF00FF; font-size: 12px; font-weight: bold;'>{message}</span>"
        elif "로직 실행" in message and ("실행 시작" in message or "반복 완료" in message):
            formatted_message = f"<span style='color: #0000FF; font-size: 20px; font-weight: bold;'>{message}</span>"
        elif "마우스 왼쪽 버튼 클릭" in message:
            formatted_message = f"<span style='color: #E2C000; font-size: 20px; font-weight: bold;'>{message}</span>"
        else:
            formatted_message = message

        # BaseLogManager를 통해 로그 출력
        self.modal_log_manager.log(
            message=formatted_message,
            level="INFO",
            modal_name="로직실행",
            include_time=include_time,
            print_to_terminal=print_to_terminal
        )

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
            
            self.execution_state_changed.emit(self.execution_state.copy())

    def save_logics_to_settings(self):
        """현재 로직 목록을 설정에 저장"""
        try:
            # 현재 설정을 다시 로드하여 최신 상태 유지
            # self.settings_manager.reload_settings()
            
            # 로직 목록을 순회하면서 order 값 업데이트
            updated_logics = {}
            # for i in range(self.SavedLogicList__QListWidget.count()):
            #     item = self.SavedLogicList__QListWidget.item(i)
            #     if item:
            #         logic_id = item.data(Qt.UserRole)
            #         if logic_id in self.settings_manager.settings.get('logics', {}):
            #             logic_info = self.settings_manager.settings['logics'][logic_id]
                        
            #             # 첫 번째 아이템의 order는 1로 설정하고, 나머지 2부터 순차적으로 증가
            #             logic_info['order'] = 1 if i == 0 else i + 1
            #             logic_info['updated_at'] = datetime.now().isoformat()
                        
            #             # settings_manager를 통해 로직 저장 (필드 순서 정)
            #             updated_logic = self.settings_manager.save_logic(logic_id, logic_info)
            #             updated_logics[logic_id] = updated_logic
            
            # # 모든 로직이 성공적으로 저장되면 saved_logics 업데이트
            # self.saved_logics = updated_logics
            
            # # settings_manager의 settings 업데이트 및 저장
            # settings = self.settings_manager.settings.copy()
            # settings['logics'] = updated_logics
            # self.settings_manager._save_settings(settings)  # settings 인자 추가
            
            self.log_message.emit("로직이 성공적으로 저장되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"로직 저장 중 오류 발생: {str(e)}")
            # 오류 발생 시 저장된 로직 다시 불러기
            # self.load_saved_logics()

    def execute_logic(self, logic_id, repeat_count=None):
        """로직을 실행"""
        try:
            # 실행 시점에 최신 로직 데이터 로드
            logics = self.logic_manager.get_all_logics(force=True)
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
            self.modal_log_manager.log(
                message=f"로직 실행 중 오류 발생: {str(e)}",
                level="ERROR",
                modal_name="로직실행",
                print_to_terminal=True
            )
            raise
        finally:
            self.running = False
            self.stop_requested = False

    def _execute_text_input(self, item):
        """텍스트 입력 실행"""
        try:
            text = item.get('text', '')
            # 텍스트 입력을 시스템 클립보드에 복사
            QApplication.clipboard().setText(text)
            
            self.modal_log_manager.log(
                message=f"텍스트 입력이 시작되었습니다: {text}",
                level="INFO",
                modal_name="로직실행",
                include_time=True
            )
            
            # 클립보드의 내용을 붙여넣기
            self.modal_log_manager.log(
                message="Ctrl+V 키 입력을 시작합니다",
                level="DEBUG",
                modal_name="로직실행",
                include_time=True
            )
            
            win32api.keybd_event(win32con.VK_CONTROL, 0, 0, 0)  # Ctrl 키 누르기
            win32api.keybd_event(0x56, 0, 0, 0)  # V 키 누르기
            win32api.keybd_event(0x56, 0, win32con.KEYEVENTF_KEYUP, 0)  # V 키 떼기
            win32api.keybd_event(win32con.VK_CONTROL, 0, win32con.KEYEVENTF_KEYUP, 0)  # Ctrl 키 떼기
            
            self.modal_log_manager.log(
                message="텍스트가 성공적으로 붙여넣기 되었습니다",
                level="INFO",
                modal_name="로직실행",
                include_time=True
            )
            
        except Exception as e:
            self.modal_log_manager.log(
                message=f"텍스트 입력 실행 중 오류 발생: {str(e)}",
                level="ERROR", 
                modal_name="로직실행",
                include_time=True,
                print_to_terminal=True
            )
