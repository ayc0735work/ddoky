from PySide6.QtCore import QObject, Signal
from BE.log.base_log_manager import BaseLogManager
from BE.settings.logics_data_settingfiles_manager import LogicsDataSettingFilesManager
from BE.function.make_logic.repository_and_service.all_logics_data_repository_and_service import LogicManager

class LogicDetailDataManageRepository(QObject):
    """로직 아이템을 관리하는 저장소 클래스"""
    
    # 시그널 정의
    logic_detail_item_added = Signal(dict)  # 아이템이 추가되었을 때
    logic_detail_item_deleted = Signal(dict)  # 아이템이 삭제되었을 때
    logic_detail_item_moved = Signal()  # 아이템이 이동되었을 때
    logic_detail_items_cleared = Signal()  # 모든 아이템이 삭제되었을 때
    logic_saved = Signal(dict)  # 로직이 저장되었을 때
    logic_loaded = Signal(dict)  # 로직이 로드되었을 때
    logic_updated = Signal(str, dict)  # 로직이 업데이트되었을 때 (이전 이름, 새 데이터)
    
    def __init__(self):
        super().__init__()
        self.items = []  # 아이템 목록
        self.base_log_manager = BaseLogManager.instance()
        self.settings_manager = LogicsDataSettingFilesManager()
        self.logic_manager = LogicManager(self.settings_manager)
        self.current_logic_id = None
        self.current_logic = None
        
    def get_logic_detail_items_next_order(self) -> int:
        """다음 순서 번호를 반환합니다.
        
        Returns:
            int: 다음 순서 번호 (현재 최대 order + 1 또는 빈 목록인 경우 1)
        """
        if not self.items:
            return 1
        return max(item.get('order', 0) for item in self.items) + 1
        
    def get_logic_detail_items(self) -> list:
        """모든 아이템을 반환합니다.
        
        Returns:
            list: 저장된 모든 아이템의 목록
        """
        return self.items.copy()  # 복사본을 반환하여 외부 수정 방지
        
    def add_logic_detail_item(self, item_info: dict):
        """아이템을 추가합니다."""
        if not isinstance(item_info, dict):
            self.base_log_manager.log(
                message=f"잘못된 형식의 데이터: {type(item_info)}",
                level="ERROR",
                file_name="logic_detail_data_manage_repository",
                method_name="add_logic_detail_item"
            )
            return
            
        # order 값이 없으면 다음 순서로 설정
        if 'order' not in item_info:
            item_info['order'] = self.get_logic_detail_items_next_order()
            
        # 아이템 추가 및 로그
        self.items.append(item_info)
        self.base_log_manager.log(
            message=f"아이템이 추가되었습니다: {item_info}",
            level="INFO",
            file_name="logic_detail_data_manage_repository",
            method_name="add_logic_detail_item"
        )
        self.logic_detail_item_added.emit(item_info)
        
    def delete_logic_detail_items(self, item_info: dict):
        """아이템을 삭제합니다."""
        if item_info in self.items:
            self.items.remove(item_info)
            self.base_log_manager.log(
                message=f"아이템이 삭제되었습니다: {item_info}",
                level="INFO",
                file_name="logic_detail_data_manage_repository",
                method_name="delete_logic_detail_items"
            )
            self.logic_detail_item_deleted.emit(item_info)
            self._reorder_logic_detail_items()
            
    def move_logic_detail_item_up(self, item_info: dict):
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
                
                self.base_log_manager.log(
                    message=f"아이템을 위로 이동했습니다: {item_info}",
                    level="INFO",
                    file_name="logic_detail_data_manage_repository",
                    method_name="move_logic_detail_item_up"
                )
                self.logic_detail_item_moved.emit()
        except ValueError:
            self.base_log_manager.log(
                message=f"아이템을 찾을 수 없습니다: {item_info}",
                level="ERROR",
                file_name="logic_detail_data_manage_repository",
                method_name="move_logic_detail_item_up"
            )
                
    def move_logic_detail_item_down(self, item_info: dict):
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
                
                self.base_log_manager.log(
                    message=f"아이템을 아래로 이동했습니다: {item_info}",
                    level="INFO",
                    file_name="logic_detail_data_manage_repository",
                    method_name="move_logic_detail_item_down"
                )
                self.logic_detail_item_moved.emit()
        except ValueError:
            self.base_log_manager.log(
                message=f"아이템을 찾을 수 없습니다: {item_info}",
                level="ERROR",
                file_name="logic_detail_data_manage_repository",
                method_name="move_logic_detail_item_down"
            )
                
    def get_logic_detail_items_count(self) -> int:
        """아이템 개수를 반환합니다."""
        return len(self.items)
        
    def clear_logic_detail_items(self):
        """모든 아이템을 삭제합니다."""
        self.items.clear()
        self.base_log_manager.log(
            message="모든 아이템이 삭제되었습니다",
            level="INFO",
            file_name="logic_detail_data_manage_repository",
            method_name="clear_logic_detail_items"
        )
        self.logic_detail_items_cleared.emit()
        
    def _reorder_logic_detail_items(self):
        """아이템들의 순서를 재정렬합니다."""
        for i, item in enumerate(self.items, 1):
            item['order'] = i 
        
    def save_logic_detail_items(self, logic_info: dict) -> tuple[bool, str]:
        """로직을 저장합니다.
        
        Args:
            logic_info (dict): 저장할 로직 정보
            
        Returns:
            tuple[bool, str]: (성공 여부, 결과 메시지)
        """
        try:
            # 1. 기본 데이터 검증
            if not logic_info.get('name'):
                return False, "로직 이름이 필요합니다."
                
            if not logic_info.get('items'):
                return False, "최소 하나의 아이템이 필요합니다."

            # 2. 이름 중복 검사 (수정 모드가 아닐 때만)
            if not self.current_logic_id:
                logics = self.settings_manager.load_logics()
                for logic in logics.values():
                    if (logic.get('name') == logic_info['name'] and 
                        not logic.get('is_nested', False)):
                        return False, "동일한 이름의 로직이 이미 존재합니다."
            
            # 3. 시간 정보와 순서 정보 추가
            from datetime import datetime
            logic_info['updated_at'] = datetime.now().isoformat()
            
            if not self.current_logic_id:  # 새 로직인 경우
                logic_info['created_at'] = datetime.now().isoformat()
                # 새 로직의 order는 기존 로직들의 최대 order + 1
                logics = self.settings_manager.load_logics()
                max_order = max([l.get('order', 0) for l in logics.values() if l.get('order', 0) > 0], default=0)
                logic_info['order'] = max_order + 1
            else:  # 수정인 경우
                logic_info['created_at'] = self.current_logic.get('created_at')
                logic_info['order'] = self.current_logic.get('order')
            
            # 4. LogicManager를 통해 저장
            success, result = self.logic_manager.save_logic(
                self.current_logic_id, 
                logic_info
            )
            
            if success:
                if self.current_logic_id:  # 수정 모드
                    self.logic_updated.emit(self.current_logic.get('name'), logic_info)
                else:  # 새 로직
                    self.logic_saved.emit(logic_info)
                    
                self.base_log_manager.log(
                    message=f"로직 '{logic_info['name']}'이(가) 저장되었습니다",
                    level="INFO",
                    file_name="logic_detail_data_manage_repository",
                    method_name="save_logic_detail_items"
                )
                return True, "저장 성공"
            else:
                self.base_log_manager.log(
                    message=f"저장 실패: {result}",
                    level="ERROR",
                    file_name="logic_detail_data_manage_repository",
                    method_name="save_logic_detail_items"
                )
                return False, result
                
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 저장 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_detail_data_manage_repository",
                method_name="save_logic_detail_items",
                print_to_terminal=True
            )
            return False, str(e)
            
    def load_logic_detail_items(self, logic_info: dict) -> bool:
        """로직을 로드합니다.
        
        Args:
            logic_info (dict): 로드할 로직 정보
            
        Returns:
            bool: 로드 성공 여부
        """
        try:
            # 1. 기본 데이터 검증
            if not logic_info or not isinstance(logic_info, dict):
                self.base_log_manager.log(
                    message="잘못된 로직 정보입니다",
                    level="ERROR",
                    file_name="logic_detail_data_manage_repository",
                    method_name="load_logic_detail_items",
                    print_to_terminal=True
                )
                return False
                
            # 2. 현재 로직 정보 초기화
            self.clear_logic_detail_items()
            
            # 3. UUID 설정 및 검증
            self.current_logic_id = logic_info.get('id')
            if not self.current_logic_id:  # ID가 없는 경우 이름으로 찾기
                logics = self.settings_manager.load_logics()
                for logic_id, saved_logic in logics.items():
                    if saved_logic.get('name') == logic_info.get('name'):
                        self.current_logic_id = logic_id
                        break
                        
            if not self.current_logic_id:
                self.base_log_manager.log(
                    message=f"로직 '{logic_info.get('name')}'의 ID를 찾을 수 없습니다",
                    level="WARNING",
                    file_name="logic_detail_data_manage_repository",
                    method_name="load_logic_detail_items"
                )
                return False
            
            # 4. 현재 로직 정보 저장
            self.current_logic = logic_info.copy()
            self.current_logic['id'] = self.current_logic_id
            
            # 5. 아이템 로드 및 display_text 설정
            items = logic_info.get('items', [])
            if isinstance(items, list):
                sorted_items = sorted(items, key=lambda x: x.get('order', float('inf')))
                for item in sorted_items:
                    if isinstance(item, dict):
                        # display_text 설정
                        if item.get('type') == 'delay':
                            item['display_text'] = f"지연시간 : {item.get('duration', 0.0)}초"
                        elif item.get('type') == 'logic':
                            item['display_text'] = item.get('logic_name', '')
                        self.add_logic_detail_item(item)
                        
            self.logic_loaded.emit(logic_info)
            self.base_log_manager.log(
                message=f"로직 '{logic_info.get('name')}'이(가) 로드되었습니다",
                level="INFO",
                file_name="logic_detail_data_manage_repository",
                method_name="load_logic_detail_items"
            )
            return True
            
        except Exception as e:
            self.base_log_manager.log(
                message=f"로직 로드 중 오류 발생: {str(e)}",
                level="ERROR",
                file_name="logic_detail_data_manage_repository",
                method_name="load_logic_detail_items"
            )
            return False
            
    def clear_current_logic_detail_item(self):
        """현재 로직 정보를 초기화합니다."""
        self.current_logic_id = None
        self.current_logic = None
        self.clear_logic_detail_items() 