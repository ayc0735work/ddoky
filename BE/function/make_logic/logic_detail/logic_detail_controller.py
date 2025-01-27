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

    def get_logic_data(self):
        """로직 데이터를 구성하고 반환"""
        # 가장 큰 order 값 찾기
        logics = self.widget.settings_manager.load_logics(force=True)
        max_order = 0
        for logic in logics.values():
            order = logic.get('order', 0)
            if order > max_order:
                max_order = order

        data = {
            'order': max_order + 1,  # 가장 큰 order + 1
            'name': self.widget.LogicNameInput__QLineEdit.text(),
            'repeat_count': self.widget.RepeatCountInput__QSpinBox.value(),
            'items': self.get_logic_detail_items(),
            'is_nested': self.widget.is_nested_checkbox.isChecked()
        }
        
        # 중첩로직이 아닐 경우에만 트리거 키 추가
        if not data['is_nested']:
            # trigger_key_info가 있고 modifiers_key_flag가 정수가 아닌 경우 변환
            if self.widget.trigger_key_info and 'modifiers_key_flag' in self.widget.trigger_key_info:
                trigger_key = self.widget.trigger_key_info.copy()
                if not isinstance(trigger_key['modifiers_key_flag'], int):
                    trigger_key['modifiers_key_flag'] = trigger_key['modifiers_key_flag'].value
                data['trigger_key'] = trigger_key
            else:
                data['trigger_key'] = self.widget.trigger_key_info
            
        self.logic_data_changed.emit(data)
        return data

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
        """로직 정보 초기화"""
        try:
            # 로직 이름 초기화
            self.widget.LogicNameInput__QLineEdit.clear()
            
            # 트리거 키 초기화
            self.widget.TriggerEnteredKeyInfoDialog__EnteredKeyInfoDialog.clear_key()
            self.widget.trigger_key_info = {}
            
            # 반복 횟수 초기화
            self.widget.RepeatCountInput__QSpinBox.setValue(1)
            
            # 중첩로직용 체크박스 초기화
            self.widget.is_nested_checkbox.setChecked(False)
            
            # 로직 아이템 목록 초기화
            self.widget.LogicItemList__QListWidget.clear()
            
            # 로직 아이템 정보 초기화
            self.widget.logic_items.clear()
            
            # 현재 편집 중인 로직 ID 초기화
            self.widget.current_logic_id = None
            
            self.base_log_manager.log(
                message="로직 정보가 초기화되었습니다",
                level="INFO",
                file_name="logic_detail_controller",
                method_name="clear_logic_info"
            )
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 정보 초기화 중 오류 발생: {str(e)}",
                level="ERROR", 
                file_name="logic_detail_controller",
                method_name="clear_logic_info"
            )

    def get_logic_detail_items(self):
        """현재 아이템 목록을 반환"""
        items = self.widget.logic_detail_data_repository_and_service.get_logic_detail_items()
        
        # 키 입력 아이템의 modifiers_key_flag를 정수로 변환
        for item in items:
            if item.get('type') == 'key' and 'modifiers_key_flag' in item:
                if not isinstance(item['modifiers_key_flag'], int):
                    item['modifiers_key_flag'] = item['modifiers_key_flag'].value
        
        return items
