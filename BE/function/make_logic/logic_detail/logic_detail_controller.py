from PySide6.QtCore import Signal, QObject
from BE.log.base_log_manager import BaseLogManager
from PySide6.QtWidgets import QListWidgetItem
from PySide6.QtCore import Qt

class LogicDetailController(QObject):
    """로직 상세 위젯의 동작을 제어하는 컨트롤러"""
    
    # 시그널 추가
    logic_data_changed = Signal(dict)  # 로직 데이터가 변경되었을 때 발생하는 시그널
    
    def __init__(self, widget):
        """
        Args:
            widget (LogicDetailWidget): 제어할 로직 상세 위젯
        """
        super().__init__()
        self.widget = widget
        self.base_log_manager = BaseLogManager.instance()
        self.connect_signals()
        
    def connect_signals(self):
        """위젯의 시그널을 처리하는 메서드들과 연결"""
        self.widget.item_moved.connect(self._handle_item_moved)
        self.widget.item_edited.connect(self._handle_item_edited)
        self.widget.item_deleted.connect(self._handle_item_deleted)
        
    def _handle_item_moved(self):
        """아이템 이동 처리"""
        self.base_log_manager.log(
            message="로직 구성 순서가 변경되었습니다",
            level="INFO",
            file_name="logic_detail_controller"
        )
        
    def _handle_item_edited(self, item_text):
        """아이템 수정 처리"""
        self.base_log_manager.log(
            message=f"수정된 로직 구성: {item_text}",
            level="INFO",
            file_name="logic_detail_controller"
        )
        
    def _handle_item_deleted(self, item_text):
        """아이템 삭제 처리"""
        self.base_log_manager.log(
            message=f"삭제된 로직 구성: {item_text}",
            level="INFO",
            file_name="logic_detail_controller"
        )
        
    def on_logic_selected(self, logic_name):
        """로직이 선택되었을 때의 처리
        
        Args:
            logic_name (str): 선택된 로직의 이름
        """
        self.base_log_manager.log(
            message=f"로직 '{logic_name}'이(가) 선택되었습니다",
            level="INFO",
            file_name="logic_detail_controller"
        )

    def get_logic_data(self) -> dict:
        """현재 로직 데이터를 반환합니다.
        
        Returns:
            dict: 현재 로직 데이터
        """
        # 위젯에서 현재 상태 가져오기
        logic_data = {
            'name': self.widget.LogicNameInput__QLineEdit.text(),
            'repeat_count': self.widget.RepeatCountInput__QSpinBox.value(),
            'is_nested': self.widget.is_nested_checkbox.isChecked(),
            'trigger_key': self.widget.trigger_key_info,
            'items': self.widget.logic_detail_data_repository_and_service.get_logic_detail_items()
        }
        
        # 현재 로직 ID가 있다면 포함
        if hasattr(self.widget, 'current_logic_id') and self.widget.current_logic_id:
            logic_data['id'] = self.widget.current_logic_id
            
        return logic_data

    def set_logic_data(self, logic_data):
        """로직 데이터 설정"""
        self.widget.LogicNameInput__QLineEdit.setText(logic_data.get('name', ''))
        self.widget.RepeatCountInput__QSpinBox.setValue(logic_data.get('repeat_count', 1))
        
        # 리스트 위젯 아이템 설정
        self.widget.LogicItemList__QListWidget.clear()  # 기존 아이템 모두 제거
        for item_data in logic_data.get('items', []):
            list_item = QListWidgetItem(item_data.get('logic_detail_item_dp_text', ''))
            list_item.setData(Qt.UserRole, item_data)
            self.widget.LogicItemList__QListWidget.addItem(list_item)
        
        # 중첩로직 여부 설정
        is_nested = logic_data.get('is_nested', False)
        self.widget.is_nested_checkbox.setChecked(is_nested)
        
        # 중첩로직이 아닐 경우에만 트리거 키 설정
        if not is_nested:
            self.widget.trigger_key_info = logic_data.get('trigger_key')
            if self.widget.trigger_key_info:
                self.widget.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog.set_key_info(self.widget.trigger_key_info)

    def clear_logic_info(self):
        """로직 정보를 초기화합니다."""
        # 기본 데이터로 초기화
        empty_logic = {
            'name': '',
            'repeat_count': 1,
            'is_nested': True,
            'trigger_key': None,
            'items': []
        }
        
        # UI 업데이트를 위해 시그널 발생
        self.logic_data_changed.emit(empty_logic)

    def get_logic_detail_items(self):
        """현재 아이템 목록을 반환"""
        items = self.widget.logic_detail_data_repository_and_service.get_logic_detail_items()
        
        # 키 입력 아이템의 modifiers_key_flag를 정수로 변환
        for item in items:
            if item.get('type') == 'key' and 'modifiers_key_flag' in item:
                if not isinstance(item['modifiers_key_flag'], int):
                    item['modifiers_key_flag'] = item['modifiers_key_flag'].value
        
        return items
