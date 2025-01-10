class EtcFunctionController:
    """기타 기능 컨트롤러"""
    
    def __init__(self, widget):
        """
        Args:
            widget: EtcFunctionWidget 인스턴스
        """
        self.widget = widget
        self._setup_connections()
        
    def _setup_connections(self):
        """시그널/슬롯 연결 설정"""
        # 카운트다운 값 변경 시그널 연결
        self.widget.countdown_value_changed.connect(self._handle_countdown_value_changed)
        
    def _handle_countdown_value_changed(self, value):
        """카운트다운 값 변경 처리"""
        # 여기서 필요한 추가 처리를 할 수 있습니다.
        pass
        
    def get_countdown_value(self):
        """현재 설정된 카운트다운 값을 반환"""
        return self.widget.countdown_spinbox.value()
