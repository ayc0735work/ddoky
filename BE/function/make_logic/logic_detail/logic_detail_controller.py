from PySide6.QtCore import Signal, QObject

class LogicDetailController(QObject):
    """로직 상세 위젯의 동작을 제어하는 컨트롤러"""
    
    # 시그널 정의
    log_message = Signal(str)  # 로그 메시지를 전달하는 시그널
    
    def __init__(self, widget):
        """
        Args:
            widget (LogicDetailWidget): 제어할 로직 상세 위젯
        """
        super().__init__()
        self.widget = widget
        self.connect_signals()
        
    def connect_signals(self):
        """위젯의 시그널을 처리하는 메서드들과 연결"""
        self.widget.item_moved.connect(self._handle_item_moved)
        self.widget.item_edited.connect(self._handle_item_edited)
        self.widget.item_deleted.connect(self._handle_item_deleted)
        
    def _handle_item_moved(self):
        """아이템 이동 처리"""
        self.log_message.emit("로직 구성 순서가 변경되었습니다.")
        
    def _handle_item_edited(self, item_text):
        """아이템 수정 처리"""
        self.log_message.emit(f"수정된 로직 구성: {item_text}")
        
    def _handle_item_deleted(self, item_text):
        """아이템 삭제 처리"""
        self.log_message.emit(f"삭제된 로직 구성: {item_text}")
        
    def on_logic_selected(self, logic_name):
        """로직이 선택되었을 때의 처리
        
        Args:
            logic_name (str): 선택된 로직의 이름
        """
