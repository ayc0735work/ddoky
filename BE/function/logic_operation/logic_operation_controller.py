from PySide6.QtWidgets import QDialog
from PySide6.QtCore import QObject, QTimer
from BE.function.logic_operation.logic_operation_widget import LogicOperationWidget
from BE.function._common_components.window_process_handler import ProcessManager
from BE.log.base_log_manager import BaseLogManager
from BE.settings.force_stop_key_data_settingfile import ForceStopKeyDataSettingFilesManager
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog
import win32con
import win32api
import time

class LogicOperationController(QObject):
    """로직 동작 허용 여부 온오프 컨트롤러"""
    
    def __init__(self, widget):
        try:
            self.widget = widget
            self.base_log_manager = BaseLogManager.instance()
            self.force_stop_key_manager = ForceStopKeyDataSettingFilesManager.instance()
            self.base_log_manager.log(
                message="LogicOperationController 초기화 시작",
                level="DEBUG",
                file_name="logic_operation_controller", 
                method_name="__init__"
            )
            super().__init__()
            self.setup_connections()
            
            # 활성 프로세스 업데이트 타이머 설정
            self.active_process_timer = QTimer()
            self.active_process_timer.timeout.connect(self._update_active_process)
            self.active_process_timer.start(100)  # 100ms 간격으로 업데이트
            self.base_log_manager.log(
                message="LogicOperationController 초기화 완료",
                level="DEBUG",
                file_name="logic_operation_controller",
                method_name="__init__"
            )
        except Exception as e:
            self.base_log_manager.log(
                message=f"컨트롤러 초기화 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_operation_controller",
                method_name="__init__"
            )
        
    def setup_connections(self):
        """시그널 연결 설정"""
        self.base_log_manager.log(
            message="컨트롤러의 시그널 연결을 설정합니다",
            level="DEBUG",
            file_name="logic_operation_controller",
            method_name="setup_connections"
        )
        self.widget.operation_toggled.connect(self._handle_operation_toggle)
        self.widget.process_reset.connect(self._handle_process_reset)
        self.widget.process_selected.connect(self._handle_process_selected)
        self.widget.select_process_btn.clicked.connect(self._handle_process_selection)
        self.widget.force_stop.connect(self._handle_force_stop)
        self.widget.edit_force_stop_key_btn.clicked.connect(self._handle_edit_force_stop_key)
        self.widget.reset_force_stop_key_btn.clicked.connect(self._handle_reset_force_stop_key)
        self.base_log_manager.log(
            message="시그널 연결이 완료되었습니다",
            level="DEBUG",
            file_name="logic_operation_controller",
            method_name="setup_connections"
        )
        
    def _handle_operation_toggle(self, checked):
        """로직 동작 허용 여부 토글 처리"""
        if checked:
            self.base_log_manager.log(
                message="로직 동작이 활성화되었습니다",
                level="INFO",
                file_name="logic_operation_controller",
                method_name="_handle_operation_toggle"
            )
        elif not checked and self.widget.logic_executor:
            # LogicExecutor의 인스턴스를 사용하여 모니터링 중지
            self.widget.logic_executor.stop_monitoring()
            self.base_log_manager.log(
                message="프로세스에서 로직 동작을 종료합니다",
                level="INFO",
                file_name="logic_operation_controller",
                method_name="_handle_operation_toggle"
            )
        
    def _handle_process_reset(self):
        """프로세스 초기화 처리"""
        self.base_log_manager.log(
            message="선택된 프로세스를 초기화 했습니다",
            level="INFO",
            file_name="logic_operation_controller", 
            method_name="_handle_process_reset"
        )
        
    def _handle_process_selected(self, process_info):
        """프로세스 선택 처리"""
        pass
        
    def _handle_process_selection(self):
        """프로세스 선택 처리"""
        # TODO: 실제 프로세스 선택 처리 구현
        pass
        
    def _handle_force_stop(self):
        """강제 중지 처리"""
        if hasattr(self.widget, 'logic_executor'):
            if self.widget.logic_executor is not None:
                self.widget.logic_executor.force_stop()
                self.widget.logic_executor.cleanup_finished.connect(self._on_force_stop_cleanup_finished)
            else:
                self.base_log_manager.log(
                    message="logic_executor가 None입니다",
                    level="DEBUG",
                    file_name="logic_operation_controller",
                    method_name="_handle_force_stop"
                )
        else:
            self.base_log_manager.log(
                message="logic_executor가 존재하지 않습니다",
                level="DEBUG",
                file_name="logic_operation_controller",
                method_name="_handle_force_stop"
            )
        
    def _on_force_stop_cleanup_finished(self):
        """강제 중지 정리 작업 완료 후 처리"""
        if hasattr(self.widget, 'logic_executor'):
            if self.widget.logic_executor is not None:
                self.widget.logic_executor.cleanup_finished.disconnect(self._on_force_stop_cleanup_finished)
                self.widget.logic_executor.start_monitoring()  # 키 감지 다시 시작
                self.base_log_manager.log(
                    message="강제 중지 정리 작업이 완료되었습니다",
                    level="INFO",
                    file_name="logic_operation_controller",
                    method_name="_on_force_stop_cleanup_finished"
                )

    def _update_active_process(self):
        """활성 프로세스 정보 업데이트"""
        process = ProcessManager.get_active_process()
        if process:
            text = f"활성 프로세스 : [ PID : {process['pid']} ] {process['name']} - {process['title']}"
            self.widget.active_process_label.setText(text)
        else:
            self.widget.active_process_label.setText("활성 프로세스 : 없음")

    def _handle_edit_force_stop_key(self):
        """강제 중지 키 수정 처리"""
        try:
            # EnteredKeyInfoDialog를 사용하여 키 입력 받기
            dialog = EnteredKeyInfoDialog(self.widget)
            
            # 다이얼로그를 모달로 실행하고 결과 확인
            result = dialog.exec()
            
            # 다이얼로그가 승인되었을 때만 처리
            if result == QDialog.Accepted:
                key_info = dialog.get_entered_key_info_result()
                if key_info:
                    # LogicExecutor에 새로운 강제 중지 키 정보 전달
                    if self.widget.logic_executor:
                        self.widget.logic_executor.set_force_stop_key(key_info['virtual_key'])
                    
                    # 설정 파일에 저장
                    if self.force_stop_key_manager.save_force_stop_key(key_info):
                        # UI 업데이트를 위해 위젯에 신호 전달
                        self.widget.update_force_stop_key_display(key_info)
                        
                        self.base_log_manager.log(
                            message=f"로직 강제 중지 키가 '{key_info['simple_display_text']}'(으)로 변경되었습니다",
                            level="INFO",
                            file_name="logic_operation_controller",
                            method_name="_handle_edit_force_stop_key"
                        )
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"강제 중지 키 설정 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_operation_controller",
                method_name="_handle_edit_force_stop_key",
                print_to_terminal=True
            )

    def _handle_reset_force_stop_key(self):
        """강제 중지 키 초기화 처리"""
        try:
            # ESC 키로 초기화
            default_key = {
                "type": "key_input",
                "key_code": "ESC",
                "scan_code": 1,
                "virtual_key": 27,
                "modifiers_key_flag": 0,
                "simple_display_text": "ESC"
            }
            
            # LogicExecutor에 초기화된 강제 중지 키 정보 전달
            if self.widget.logic_executor:
                self.widget.logic_executor.set_force_stop_key(27)
                
            # 설정 파일에 저장
            if self.force_stop_key_manager.save_force_stop_key(default_key):
                # UI 업데이트를 위해 위젯에 신호 전달
                self.widget.update_force_stop_key_display(default_key)
                
                self.base_log_manager.log(
                    message="로직 강제 중지 키가 'ESC'로 초기화되었습니다",
                    level="INFO",
                    file_name="logic_operation_controller",
                    method_name="_handle_reset_force_stop_key"
                )
        except Exception as e:
            self.base_log_manager.log(
                message=f"강제 중지 키 초기화 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_operation_controller",
                method_name="_handle_reset_force_stop_key",
                print_to_terminal=True
            )
