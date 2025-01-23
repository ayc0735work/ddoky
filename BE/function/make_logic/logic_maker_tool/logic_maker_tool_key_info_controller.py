from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog
from BE.log.manager.base_log_manager import BaseLogManager

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
    
    def handle_confirmed_key_input(self, get_entered_key_info):
        """확인된 키 입력 정보를 처리
        
        Args:
            get_entered_key_info (dict): EnteredKeyInfoDialog에서 받은 키 입력 정보
            
        데이터 흐름:
        1. 로그 메시지 생성 및 전달
        2. 키 상태 정보 생성 (누르기/떼기)
        3. 각 상태 정보를 내부 처리 메서드로 전달
        """
        self.modal_log_manager.log(
            message=f"키 입력 정보가 전달되었습니다.: {get_entered_key_info.get(str(get_entered_key_info))} <br>",
            level="INFO", 
            modal_name="로직_메이커_툴_키_정보_컨트롤러"
        )
        
        # 누르기 이벤트용 키 상태 정보
        key_state_info_press = get_entered_key_info.copy()
        key_state_info_press['type'] = "key"
        key_state_info_press['action'] = "누르기"
        key_state_info_press['display_text'] = f"{get_entered_key_info['key_code']} --- 누르기"

        self.modal_log_manager.log(
            message=f"키 상태 정보가 생성되었습니다. : {key_state_info_press.get(str(key_state_info_press))} <br>",
            level="INFO", 
            modal_name="로직_메이커_툴_키_정보_컨트롤러"
        )

        # 누르기 이벤트 처리
        self._process_key_state_info(key_state_info_press)

        # 떼기 이벤트용 키 상태 정보
        key_state_info_release = get_entered_key_info.copy()
        key_state_info_release['type'] = "key"
        key_state_info_release['action'] = "떼기"
        key_state_info_release['display_text'] = f"{get_entered_key_info['key_code']} --- 떼기"

        self.modal_log_manager.log(
            message=f"키 상태 정보가 생성되었습니다. : {key_state_info_release.get(str(key_state_info_release))} <br>",
            level="INFO", 
            modal_name="로직_메이커_툴_키_정보_컨트롤러"
        )

        # 떼기 이벤트 처리
        self._process_key_state_info(key_state_info_release)

    def _process_key_state_info(self, key_state_info):
        """키 상태 정보를 처리하는 내부 메서드
        
        Args:
            key_state_info (dict): 처리할 키 상태 정보
        """
        # UI 업데이트를 위한 시그널 발생
        self.item_added.emit(key_state_info)
        
        # 로그 메시지 출력
        self.modal_log_manager.log(
            message=f"키 입력 정보가 전달되었습니다.: {key_state_info.get(str(key_state_info))} <br>",
            level="INFO", 
            modal_name="로직_메이커_툴_키_정보_컨트롤러"
        )
