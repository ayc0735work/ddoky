class AdvancedController:
    """고급 기능 위젯의 동작을 제어하는 컨트롤러"""
    
    def __init__(self, widget):
        """
        Args:
            widget (AdvancedWidget): 제어할 고급 기능 위젯
        """
        self.widget = widget
        self.connect_signals()
        
    def connect_signals(self):
        """위젯의 시그널을 처리하는 메서드들과 연결"""
        self.widget.advanced_action.connect(self._handle_advanced_action)
        
    def _handle_advanced_action(self, action):
        """고급 기능 실행 처리
        
        Args:
            action (str): 실행된 고급 기능의 종류
        """
        log_msg = f"고급 기능이 실행되었습니다: {action}"
        self.widget.log_message.emit(log_msg)
