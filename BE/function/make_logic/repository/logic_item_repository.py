from PySide6.QtCore import QObject, Signal

class LogicItemRepository(QObject):
    """로직 아이템을 관리하는 저장소 클래스"""
    
    # 시그널 정의
    item_added = Signal(dict)  # 아이템이 추가되었을 때
    item_deleted = Signal(dict)  # 아이템이 삭제되었을 때
    item_moved = Signal()  # 아이템이 이동되었을 때
    items_cleared = Signal()  # 모든 아이템이 삭제되었을 때
    
    def __init__(self):
        super().__init__()
        self.items = []  # 아이템 목록
        
    def add_item(self, item_info: dict):
        """아이템을 추가합니다."""
        if not isinstance(item_info, dict):
            raise ValueError("item_info must be a dictionary")
            
        # order 값이 없으면 마지막 순서로 설정
        if 'order' not in item_info:
            item_info['order'] = len(self.items) + 1
            
        self.items.append(item_info)
        self.item_added.emit(item_info)
        
    def delete_item(self, item_info: dict):
        """아이템을 삭제합니다."""
        if item_info in self.items:
            self.items.remove(item_info)
            self.item_deleted.emit(item_info)
            self._reorder_items()
            
    def move_item_up(self, item_info: dict):
        """아이템을 위로 이동합니다."""
        index = self.items.index(item_info)
        if index > 0:
            self.items[index], self.items[index - 1] = self.items[index - 1], self.items[index]
            self._reorder_items()
            self.item_moved.emit()
            
    def move_item_down(self, item_info: dict):
        """아이템을 아래로 이동합니다."""
        index = self.items.index(item_info)
        if index < len(self.items) - 1:
            self.items[index], self.items[index + 1] = self.items[index + 1], self.items[index]
            self._reorder_items()
            self.item_moved.emit()
            
    def get_items(self) -> list:
        """모든 아이템을 반환합니다."""
        return self.items
        
    def get_items_count(self) -> int:
        """아이템 개수를 반환합니다."""
        return len(self.items)
        
    def clear_items(self):
        """모든 아이템을 삭제합니다."""
        self.items.clear()
        self.items_cleared.emit()
        
    def _reorder_items(self):
        """아이템들의 순서를 재정렬합니다."""
        for i, item in enumerate(self.items, 1):
            item['order'] = i 