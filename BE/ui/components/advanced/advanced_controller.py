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
        """고급 기능 액션 처리"""
        print(f"고급 기능 실행: {action}")
