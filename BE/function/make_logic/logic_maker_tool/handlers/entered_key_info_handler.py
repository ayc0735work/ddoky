from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QDialog
from BE.function._common_components.modal.entered_key_info_modal.entered_key_info_dialog import EnteredKeyInfoDialog

class EnteredKeyInfoHandler(QObject):
    """키 입력 처리를 담당하는 핸들러 클래스"""
    
    # 시그널 정의
    confirmed_and_added_key_info = Signal(dict)  # 키 입력이 확인되고 추가되었을 때
    log_message = Signal(str)  # 로그 메시지 전달용
    
    def __init__(self, parent=None):
        """초기화
        
        Args:
            parent (QObject): 부모 객체
        """
        super().__init__(parent)
    
    def request_key_input(self, parent=None):
        """키 입력을 요청하는 다이얼로그를 표시
        
        Args:
            parent (QWidget): 다이얼로그의 부모 위젯
            
        프로세스:
        1. EnteredKeyInfoDialog 인스턴스를 생성하여 모달 다이얼로그로 표시
        2. 사용자가 키를 입력하면 EnteredKeyInfoWidget이 keyboard_hook_handler를 통해 키 정보를 캡처
        3. 사용자가 확인(OK)을 클릭하면:
            - EnteredKeyInfoDialog.get_entered_key_info()를 통해 formatted_key_info를 가져옴
            - 키 정보가 유효하면 handle_confirmed_key_input()를 호출하여 처리
        """
        # 키 입력 다이얼로그 생성
        dialog = EnteredKeyInfoDialog(parent)
        
        # 다이얼로그를 모달로 실행하고 사용자 응답 확인
        if dialog.exec() == QDialog.Accepted:
            # 입력된 키 정보 가져오기
            get_entered_key_info = dialog.get_entered_key_info()
            
            # 키 정보가 유효한 경우 처리
            if get_entered_key_info:
                self.handle_confirmed_key_input(get_entered_key_info)
    
    def handle_confirmed_key_input(self, get_entered_key_info):
        """확인된 키 입력 정보를 처리
        
        Args:
            get_entered_key_info (dict): EnteredKeyInfoDialog에서 받은 키 입력 정보
            
        데이터 흐름:
        1. 로그 메시지 생성 및 전달
        2. 키 상태 정보 생성 (누르기/떼기)
        3. confirmed_and_added_key_info 시그널을 통해 키 상태 정보 전달
        """
        # 로그 메시지 생성
        self.log_message.emit(
            f"키 입력이 추가되었습니다 [ <br>"
            f"키: {get_entered_key_info['key_code']}, <br>"
            f"스캔 코드 (하드웨어 고유값): {get_entered_key_info['scan_code']}, <br>"
            f"확장 가상 키 (운영체제 레벨의 고유 값): {get_entered_key_info['virtual_key']}, <br>"
            f"키보드 위치: {get_entered_key_info['location']}, <br>"
            f"수정자 키: {get_entered_key_info['modifier_text']} ] <br>"
        )
        
        # 누르기 이벤트용 키 상태 정보
        key_state_info_press = get_entered_key_info.copy()
        key_state_info_press['type'] = "key"
        key_state_info_press['action'] = "누르기"
        key_state_info_press['display_text'] = f"{get_entered_key_info['key_code']} --- 누르기"

        self.confirmed_and_added_key_info.emit(key_state_info_press)

        # 로그 메시지 전달
        self.log_message.emit(
            f"<br>키 상태 정보가 업데이트 되었습니다. <br>"
            f"type: {key_state_info_press['type']}, <br>"
            f"action: {key_state_info_press['action']}, <br>"
            f"display_text: {key_state_info_press['display_text']}, <br>"           
            )
        
        # 떼기 이벤트용 키 상태 정보
        key_state_info_release = get_entered_key_info.copy()
        key_state_info_release['type'] = "key"
        key_state_info_release['action'] = "떼기"
        key_state_info_release['display_text'] = f"{get_entered_key_info['key_code']} --- 떼기"


        self.confirmed_and_added_key_info.emit(key_state_info_release)

        # 로그 메시지 전달
        self.log_message.emit(
            f"<br>키 상태 정보가 업데이트 되었습니다. <br>"
            f"type: {key_state_info_release['type']}, <br>"
            f"action: {key_state_info_release['action']}, <br>"
            f"display_text: {key_state_info_release['display_text']}, <br>"           
            )
    
    def handle_key_input(self, key_info):
        """키 입력 데이터 처리
        
        Args:
            key_info (dict): 입력된 키 정보
            
        처리 과정:
        1. 디버그 로그 출력
        2. 키 정보 검증
        3. 시그널 발생
        """
        # 디버그 로그 출력
        self.log_message.emit(f"[DEBUG] 키 입력 처리 시작 - 입력받은 데이터: {key_info.get('display_text', str(key_info))}")
        
        # 키 정보 검증 및 처리
        if not isinstance(key_info, dict):
            self.log_message.emit("[ERROR] 잘못된 키 입력 데이터 형식")
            return
            
        # 처리 완료 로그
        self.log_message.emit(f"[DEBUG] 키 입력 처리 완료: {key_info}")
