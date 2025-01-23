from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog
from BE.log.manager.base_log_manager import BaseLogManager
from BE.function.make_logic.repository.logic_item_repository import LogicItemRepository

class LogicMakerToolKeyInfoController(QObject):
    """키 입력 처리를 담당하는 컨트롤러 클래스"""
    
    # 시그널 정의
    item_added = Signal(dict)  # UI 업데이트용
    
    def __init__(self, parent=None):
        """초기화
        
        Args:
            parent (QObject): 부모 객체
        """
        super().__init__(parent)
        self.modal_log_manager = BaseLogManager.instance()
    
    def handle_confirmed_key_input(self, key_info):
        """확인된 키 입력을 처리합니다.
        
        Args:
            key_info (dict): 키 입력 정보를 포함하는 딕셔너리
                key_code: 입력된 키
                modifiers: 수정자 키 목록
                display_text: 표시할 텍스트
        """
        self.modal_log_manager.log(
            message=f"키 입력 처리 시작 - 입력받은 데이터: {key_info}",
            level="DEBUG",
            file_name="logic_maker_tool_key_info_controller"
        )
        
        if not isinstance(key_info, dict):
            self.modal_log_manager.log(
                message=f"잘못된 형식의 데이터: {type(key_info)}",
                level="ERROR",
                file_name="logic_maker_tool_key_info_controller"
            )
            return
            
        # 키 누르기 상태 정보 생성
        press_info = {
            'type': 'key',
            'key': key_info.get('key_code'),
            'modifiers': key_info.get('modifiers', []),
            'display_text': f"{key_info.get('simple_display_text')} --- 누르기",
            'action': '누르기',
            'scan_code': key_info.get('scan_code'),
            'virtual_key': key_info.get('virtual_key')
        }
        
        # 키 떼기 상태 정보 생성
        release_info = {
            'type': 'key',
            'key': key_info.get('key_code'),
            'modifiers': key_info.get('modifiers', []),
            'display_text': f"{key_info.get('simple_display_text')} --- 떼기",
            'action': '떼기',
            'scan_code': key_info.get('scan_code'),
            'virtual_key': key_info.get('virtual_key')
        }
        
        # 키 누르기와 떼기 상태 정보를 시그널로 전달
        self.item_added.emit(press_info)
        self.item_added.emit(release_info)
        
        self.modal_log_manager.log(
            message="키 입력 처리가 완료되었습니다",
            level="INFO",
            file_name="logic_maker_tool_key_info_controller"
        )
