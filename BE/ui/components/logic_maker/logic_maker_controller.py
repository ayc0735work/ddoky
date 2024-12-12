class LogicMakerController:
    """로직 메이커 컨트롤러"""
    
    def __init__(self, widget):
        """초기화
        
        Args:
            widget (LogicMakerWidget): 로직 메이커 위젯
        """
        self.widget = widget
        self._connect_signals()
        
    def _connect_signals(self):
        """시그널 연결"""
        self.widget.key_input.connect(self._handle_key_input)
        self.widget.mouse_input.connect(self._handle_mouse_input)
        self.widget.delay_input.connect(self._handle_delay_input)
        self.widget.record_mode.connect(self._handle_record_mode)
        
    def _handle_key_input(self, key_text):
        """키 입력 처리
        
        Args:
            key_text (str): 입력된 키 텍스트
        """
        pass
        
    def _handle_mouse_input(self, mouse_text):
        """마우스 입력 처리
        
        Args:
            mouse_text (str): 마우스 입력 텍스트
        """
        log_msg = f"(logic_maker_controller--_handle_mouse_input)마우스 입력이 추가되었습니다: {mouse_text}"
        self.widget.log_message.emit(log_msg)
        
    def _handle_delay_input(self, delay_text):
        """지연시간 처리
        
        Args:
            delay_text (str): 지연시간 텍스트
        """
        log_msg = f"지연시간이 추가되었습니다: {delay_text}"
        self.widget.log_message.emit(log_msg)
        
    def _handle_record_mode(self, is_recording):
        """기록 모드 처리
        
        Args:
            is_recording (bool): 기록 모드 활성화 여부
        """
        status = "시작" if is_recording else "중지"
        log_msg = f"기록 모드가 {status}되었습니다."
        self.widget.log_message.emit(log_msg)
        
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
