from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog
from BE.log.base_log_manager import BaseLogManager
from BE.function.make_logic.repository.logic_detail_data_manage_repository import LogicDetailDataManageRepository

class LogicMakerToolKeyInfoController(QObject):
    """키 입력 처리를 담당하는 컨트롤러 클래스"""
    
    def __init__(self, repository: LogicDetailDataManageRepository, parent=None):
        """초기화
        
        Args:
            repository (LogicDetailDataManageRepository): 아이템 관리 저장소
            parent (QObject): 부모 객체
        """
        super().__init__(parent)
        self.repository = repository
        self.base_log_manager = BaseLogManager.instance()
    
    def validate_key_info(self, key_info: dict) -> bool:
        """키 정보의 유효성을 검사합니다.
        
        Args:
            key_info (dict): 검사할 키 정보
            
        Returns:
            bool: 유효성 검사 결과
        """
        if not isinstance(key_info, dict):
            self.base_log_manager.log(
                message=f"validate_key_info - 유효성 검사 결과 잘못된 형식의 데이터: {type(key_info)}",
                level="ERROR",
                file_name="logic_maker_tool_key_info_controller", 
                method_name="validate_key_info"
            )
            return False
            
        required_fields = ['type', 'key', 'modifiers', 'scan_code', 'virtual_key']
        for field in required_fields:
            if field not in key_info:
                self.base_log_manager.log(
                    message=f"validate_key_info - 유효성 검사 결과 필수 필드 누락: {field}",
                    level="ERROR",
                    file_name="logic_maker_tool_key_info_controller", 
                    method_name="validate_key_info"
                )
                return False
                
        if key_info['type'] != 'key':
            self.base_log_manager.log(
                message=f"validate_key_info - 유효성 검사 결과 잘못된 타입: {key_info['type']}",
                level="ERROR",
                file_name="logic_maker_tool_key_info_controller", 
                method_name="validate_key_info"
            )
            return False
            
        self.base_log_manager.log(
            message=f"validate_key_info - 유효성 검사 결과 키 정보 유효(key_info): {key_info}",
            level="DEBUG",
            file_name="logic_maker_tool_key_info_controller", 
            method_name="validate_key_info"
        )
        return True
    
    def key_state_info_process(self, entered_key_info):
        """입력된 키 정보를 처리하고 저장합니다.
        
        1. 키 정보 검증
        2. 누르기/떼기 상태 정보 생성
        3. 순서 정보 부여
        4. Repository에 저장
        """
        self.base_log_manager.log(
            message=f"입력된 키에 상태값 부여 시작(entered_key_info): {entered_key_info}",
            level="DEBUG",
            file_name="logic_maker_tool_key_info_controller", 
            method_name="key_state_info_process"
        )
        
        if not isinstance(entered_key_info, dict):
            self.base_log_manager.log(
                message=f"잘못된 형식의 데이터(entered_key_info): {type(entered_key_info)}",
                level="ERROR",
                file_name="logic_maker_tool_key_info_controller", 
                method_name="key_state_info_process"
            )
            return
            
        # 키 누르기 상태 정보 생성
        pressed_key_info = {
            'type': 'key',
            'key': entered_key_info.get('key_code'),
            'modifiers': entered_key_info.get('modifiers', []),
            'modifiers_text': entered_key_info.get('modifiers_text', []),
            'location': entered_key_info.get('location', ''),
            'display_text': f"{entered_key_info.get('simple_display_text')} --- 누르기",
            'action': '누르기',
            'scan_code': entered_key_info.get('scan_code'),
            'virtual_key': entered_key_info.get('virtual_key')
        }
        
        # 키 떼기 상태 정보 생성
        released_key_info = {
            'type': 'key',
            'key': entered_key_info.get('key_code'),
            'modifiers': entered_key_info.get('modifiers', []),
            'modifiers_text': entered_key_info.get('modifiers_text', []),
            'location': entered_key_info.get('location', ''),
            'display_text': f"{entered_key_info.get('simple_display_text')} --- 떼기",
            'action': '떼기',
            'scan_code': entered_key_info.get('scan_code'),
            'virtual_key': entered_key_info.get('virtual_key')
        }
        
        # 각 키 정보 검증 및 저장
        for key_info in [pressed_key_info, released_key_info]:
            if self.validate_key_info(key_info):
                # Repository에 저장 (Repository에서 자동으로 order 부여)
                self.repository.add_logic_detail_item(key_info)
                self.base_log_manager.log(
                    message=f"키 정보 저장 완료(key_info): {key_info}",
                    level="DEBUG",
                    file_name="logic_maker_tool_key_info_controller", 
                    method_name="key_state_info_process"
                )
            else:
                self.base_log_manager.log(
                    message=f"키 정보 검증 실패(key_info): {key_info}",
                    level="ERROR",
                    file_name="logic_maker_tool_key_info_controller", 
                    method_name="key_state_info_process"
                )
        
        self.base_log_manager.log(
            message=f"키 정보 추가 최종 완료(entered_key_info): {entered_key_info}",
            level="INFO",
            file_name="logic_maker_tool_key_info_controller", 
            method_name="key_state_info_process"
        )

