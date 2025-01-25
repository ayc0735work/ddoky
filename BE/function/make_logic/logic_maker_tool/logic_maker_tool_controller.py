from PySide6.QtCore import QObject, Signal
from BE.log.base_log_manager import BaseLogManager

class LogicMakerController(QObject):
    """로직 메이커 컨트롤러"""
    
    def __init__(self, widget):
        """초기화
        
        Args:
            widget (LogicMakerToolWidget): 로직 메이커 위젯
        """
        super().__init__()
        self.widget = widget
        self.base_log_manager = BaseLogManager.instance()
        self._connect_signals()
        
    def _connect_signals(self):
        """시그널 연결"""
        self.widget.mouse_input.connect(self._handle_mouse_input)
        self.widget.delay_input.connect(self._handle_delay_input)
        self.widget.record_mode.connect(self._handle_record_mode)
        self.widget.wait_click_input.connect(self._handle_wait_click_input)
        
    def _handle_mouse_input(self, mouse_info):
        """마우스 입력 처리
        
        Args:
            mouse_info (dict): 마우스 입력 정보
        """
        # 아이템 추가
        self.widget.add_item(mouse_info)
        
        self.base_log_manager.log(
            message=f"마우스 입력이 추가되었습니다: {mouse_info['display_text']}",
            level="INFO",
            file_name="logic_maker_tool_controller"
        )
        
    def _handle_delay_input(self, delay_text):
        """지연시간 처리
        
        Args:
            delay_text (str): 지연시간 텍스트
        """
        self.base_log_manager.log(
            message=f"지연시간이 추가되었습니다: {delay_text}",
            level="INFO",
            file_name="logic_maker_tool_controller"
        )
        
    def _handle_record_mode(self, is_recording):
        """기록 모드 처리
        
        Args:
            is_recording (bool): 기록 모드 활성화 여부
        """
        status = "시작" if is_recording else "중지"
        self.base_log_manager.log(
            message=f"기록 모드가 {status}되었습니다",
            level="INFO",
            file_name="logic_maker_tool_controller"
        )
        
    def _handle_wait_click_input(self, wait_click_info):
        """클릭 대기 입력 처리
        
        Args:
            wait_click_info (dict): 클릭 대기 정보
        """
        self.base_log_manager.log(
            message=f"클릭 대기 아이템이 추가되었습니다: {wait_click_info['display_text']}",
            level="INFO",
            file_name="logic_maker_tool_controller"
        )
        
    def save_logic(self, logic_data):
        """로직 저장"""
        # 중첩로직 참조 정보 유지
        if 'items' in logic_data:
            for item in logic_data['items']:
                if item['type'] == 'logic':
                    # 중첩로직의 logic_id는 수정하지 않음
                    continue
        
        # 나머지 저장 로직 수행
        return self.logic_manager.save_logic(logic_data)
