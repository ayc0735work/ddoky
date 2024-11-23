class LogicMakerController:
    """로직 메이커 위젯의 동작을 제어하는 컨트롤러"""
    
    def __init__(self, widget):
        """
        Args:
            widget (LogicMakerWidget): 제어할 로직 메이커 위젯
        """
        self.widget = widget
        self.connect_signals()
        
    def connect_signals(self):
        """위젯의 시그널을 처리하는 메서드들과 연결"""
        self.widget.key_input_requested.connect(self._handle_key_input)
        self.widget.mouse_input_requested.connect(self._handle_mouse_input)
        self.widget.delay_input_requested.connect(self._handle_delay_input)
        self.widget.record_mode_toggled.connect(self._handle_record_mode)
        self.widget.logic_created.connect(self._handle_logic_created)
        
    def _handle_key_input(self):
        """키 입력 추가 처리"""
        print("키 입력 추가 클릭됨")
        
    def _handle_mouse_input(self):
        """마우스 입력 추가 처리"""
        print("마우스 입력 추가 클릭됨")
        
    def _handle_delay_input(self):
        """지연시간 추가 처리"""
        print("지연시간 추가 클릭됨")
        
    def _handle_record_mode(self):
        """기록 모드 토글 처리"""
        print("기록 모드 클릭됨")
        
    def _handle_logic_created(self, logic_name):
        """새로운 로직 생성 처리"""
        print(f"새로운 로직이 생성되었습니다: {logic_name}")
