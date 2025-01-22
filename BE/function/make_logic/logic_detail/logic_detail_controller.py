from PySide6.QtCore import Signal, QObject
from BE.log.manager.modal_log_manager import ModalLogManager

class LogicDetailController(QObject):
    """로직 상세 위젯의 동작을 제어하는 컨트롤러"""
    
    def __init__(self, widget):
        """
        Args:
            widget (LogicDetailWidget): 제어할 로직 상세 위젯
        """
        super().__init__()
        self.widget = widget
        self.modal_log_manager = ModalLogManager.instance()
        self.connect_signals()
        
    def connect_signals(self):
        """위젯의 시그널을 처리하는 메서드들과 연결"""
        self.widget.item_moved.connect(self._handle_item_moved)
        self.widget.item_edited.connect(self._handle_item_edited)
        self.widget.item_deleted.connect(self._handle_item_deleted)
        
    def _handle_item_moved(self):
        """아이템 이동 처리"""
        self.modal_log_manager.log(
            message="로직 구성 순서가 변경되었습니다",
            level="INFO",
            modal_name="로직상세"
        )
        
    def _handle_item_edited(self, item_text):
        """아이템 수정 처리"""
        self.modal_log_manager.log(
            message=f"수정된 로직 구성: {item_text}",
            level="INFO",
            modal_name="로직상세"
        )
        
    def _handle_item_deleted(self, item_text):
        """아이템 삭제 처리"""
        self.modal_log_manager.log(
            message=f"삭제된 로직 구성: {item_text}",
            level="INFO",
            modal_name="로직상세"
        )
        
    def on_logic_selected(self, logic_name):
        """로직이 선택되었을 때의 처리
        
        Args:
            logic_name (str): 선택된 로직의 이름
        """
        self.modal_log_manager.log(
            message=f"로직 '{logic_name}'이(가) 선택되었습니다",
            level="INFO",
            modal_name="로직상세"
        )
