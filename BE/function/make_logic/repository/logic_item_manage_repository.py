from PySide6.QtCore import QObject, Signal
from BE.log.manager.base_log_manager import BaseLogManager

class LogicItemManageRepository(QObject):
    """로직 아이템을 관리하는 저장소 클래스"""
    
    # 시그널 정의
    item_added = Signal(dict)  # 아이템이 추가되었을 때
    item_deleted = Signal(dict)  # 아이템이 삭제되었을 때
    item_moved = Signal()  # 아이템이 이동되었을 때
    items_cleared = Signal()  # 모든 아이템이 삭제되었을 때
    
    def __init__(self):
        super().__init__()
        self.items = []  # 아이템 목록
        self.modal_log_manager = BaseLogManager.instance()
        
    def get_next_order(self) -> int:
        """다음 순서 번호를 반환합니다.
        
        Returns:
            int: 다음 순서 번호 (현재 최대 order + 1 또는 빈 목록인 경우 1)
        """
        if not self.items:
            return 1
        return max(item.get('order', 0) for item in self.items) + 1
        
    def get_items(self) -> list:
        """모든 아이템을 반환합니다.
        
        Returns:
            list: 저장된 모든 아이템의 목록
        """
        return self.items.copy()  # 복사본을 반환하여 외부 수정 방지
        
    def add_item(self, item_info: dict):
        """아이템을 추가합니다."""
        if not isinstance(item_info, dict):
            self.modal_log_manager.log(
                message=f"잘못된 형식의 데이터: {type(item_info)}",
                level="ERROR",
                file_name="logic_item_manage_repository"
            )
            return
            
        # order 값이 없으면 다음 순서로 설정
        if 'order' not in item_info:
            item_info['order'] = self.get_next_order()
            
        # 아이템 추가 및 로그
        self.items.append(item_info)
        self.modal_log_manager.log(
            message=f"아이템이 추가되었습니다: {item_info}",
            level="INFO",
            file_name="logic_item_manage_repository"
        )
        self.item_added.emit(item_info)
        
    def delete_item(self, item_info: dict):
        """아이템을 삭제합니다."""
        if item_info in self.items:
            self.items.remove(item_info)
            self.modal_log_manager.log(
                message=f"아이템이 삭제되었습니다: {item_info}",
                level="INFO",
                file_name="logic_item_manage_repository"
            )
            self.item_deleted.emit(item_info)
            self._reorder_items()
            
    def move_item_up(self, item_info: dict):
        """아이템을 위로 이동합니다."""
        try:
            current_index = self.items.index(item_info)
            if current_index > 0:
                # 아이템 위치 교환
                self.items[current_index], self.items[current_index - 1] = \
                    self.items[current_index - 1], self.items[current_index]
                    
                # order 값도 교환
                self.items[current_index]['order'], self.items[current_index - 1]['order'] = \
                    self.items[current_index - 1]['order'], self.items[current_index]['order']
                
                self.modal_log_manager.log(
                    message=f"아이템을 위로 이동했습니다: {item_info}",
                    level="INFO",
                    file_name="logic_item_manage_repository"
                )
                self.item_moved.emit()
        except ValueError:
            self.modal_log_manager.log(
                message=f"아이템을 찾을 수 없습니다: {item_info}",
                level="ERROR",
                file_name="logic_item_manage_repository"
            )
                
    def move_item_down(self, item_info: dict):
        """아이템을 아래로 이동합니다."""
        try:
            current_index = self.items.index(item_info)
            if current_index < len(self.items) - 1:
                # 아이템 위치 교환
                self.items[current_index], self.items[current_index + 1] = \
                    self.items[current_index + 1], self.items[current_index]
                    
                # order 값도 교환
                self.items[current_index]['order'], self.items[current_index + 1]['order'] = \
                    self.items[current_index + 1]['order'], self.items[current_index]['order']
                
                self.modal_log_manager.log(
                    message=f"아이템을 아래로 이동했습니다: {item_info}",
                    level="INFO",
                    file_name="logic_item_manage_repository"
                )
                self.item_moved.emit()
        except ValueError:
            self.modal_log_manager.log(
                message=f"아이템을 찾을 수 없습니다: {item_info}",
                level="ERROR",
                file_name="logic_item_manage_repository"
            )
                
    def get_items_count(self) -> int:
        """아이템 개수를 반환합니다."""
        return len(self.items)
        
    def clear_items(self):
        """모든 아이템을 삭제합니다."""
        self.items.clear()
        self.modal_log_manager.log(
            message="모든 아이템이 삭제되었습니다",
            level="INFO",
            file_name="logic_item_manage_repository"
        )
        self.items_cleared.emit()
        
    def _reorder_items(self):
        """아이템들의 순서를 재정렬합니다."""
        for i, item in enumerate(self.items, 1):
            item['order'] = i 