from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog
from BE.log.manager.base_log_manager import BaseLogManager

class LogicMakerToolKeyInfoController(QObject):
    """키 입력 처리를 담당하는 핸들러 클래스"""
    
    # 시그널 정의
    confirmed_and_added_key_info = Signal(dict)  # 키 입력이 확인되고 추가되었을 때
    
    def __init__(self, parent=None):
        """초기화
        
        Args:
            parent (QObject): 부모 객체
        """
        super().__init__(parent)
        self.modal_log_manager = BaseLogManager.instance()
    
    def handle_confirmed_key_input(self, get_entered_key_info):
        """확인된 키 입력 정보를 처리
        
        Args:
            get_entered_key_info (dict): EnteredKeyInfoDialog에서 받은 키 입력 정보
            
        데이터 흐름:
        1. 로그 메시지 생성 및 전달
        2. 키 상태 정보 생성 (누르기/떼기)
        3. confirmed_and_added_key_info 시그널을 통해 키 상태 정보 전달
        """
        # 키 입력 정보 로그
        self.modal_log_manager.log(
            message=(
                f"키 입력이 추가되었습니다 [ <br>"
                f"키: {get_entered_key_info['key_code']}, <br>"
                f"스캔 코드 (하드웨어 고유값): {get_entered_key_info['scan_code']}, <br>"
                f"확장 가상 키 (운영체제 레벨의 고유 값): {get_entered_key_info['virtual_key']}, <br>"
                f"키보드 위치: {get_entered_key_info['location']}, <br>"
                f"수정자 키: {get_entered_key_info['modifier_text']} ] <br>"
            ),
            level="INFO",
            modal_name="입력된_키_정보_핸들러"
        )
        
        # 누르기 이벤트용 키 상태 정보
        key_state_info_press = get_entered_key_info.copy()
        key_state_info_press['type'] = "key"
        key_state_info_press['action'] = "누르기"
        key_state_info_press['display_text'] = f"{get_entered_key_info['key_code']} --- 누르기"

        self.confirmed_and_added_key_info.emit(key_state_info_press)

        # 키 상태 정보 업데이트 로그 (누르기)
        self.modal_log_manager.log(
            message=(
                f"키 상태 정보가 업데이트 되었습니다. <br>"
                f"type: {key_state_info_press['type']}, <br>"
                f"action: {key_state_info_press['action']}, <br>"
                f"display_text: {key_state_info_press['display_text']}"
            ),
            level="DEBUG",
            modal_name="입력된_키_정보_핸들러"
        )
        
        # 떼기 이벤트용 키 상태 정보
        key_state_info_release = get_entered_key_info.copy()
        key_state_info_release['type'] = "key"
        key_state_info_release['action'] = "떼기"
        key_state_info_release['display_text'] = f"{get_entered_key_info['key_code']} --- 떼기"

        self.confirmed_and_added_key_info.emit(key_state_info_release)

        # 키 상태 정보 업데이트 로그 (떼기)
        self.modal_log_manager.log(
            message=(
                f"키 상태 정보가 업데이트 되었습니다. <br>"
                f"type: {key_state_info_release['type']}, <br>"
                f"action: {key_state_info_release['action']}, <br>"
                f"display_text: {key_state_info_release['display_text']}"
            ),
            level="DEBUG",
            modal_name="입력된_키_정보_핸들러"
        )
