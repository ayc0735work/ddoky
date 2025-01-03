class LogicListController:
    """로직 리스트 위젯의 동작을 제어하는 컨트롤러"""
    
    def __init__(self, widget):
        """
        Args:
            widget (LogicListWidget): 제어할 로직 리스트 위젯
        """
        self.widget = widget
        self.connect_signals()
        
    def connect_signals(self):
        """위젯의 시그널을 처리하는 메서드들과 연결"""
        self.widget.item_moved.connect(self._handle_item_moved)
        self.widget.item_edited.connect(self._handle_item_edited)
        self.widget.item_deleted.connect(self._handle_item_deleted)
        self.widget.logic_selected.connect(self._handle_logic_selected)
        
    def _handle_item_moved(self):
        """아이템 이동 처리"""
        self.on_item_moved()
        
    def on_item_moved(self):
        """아이템이 이동되었을 때의 처리"""
        log_msg = "로직 순서가 변경되었습니다."
        self.widget.log_message.emit(log_msg)
        
    def _handle_item_edited(self, item_text):
        """아이템 수정 처리"""
        self.on_item_edited(item_text)
        
    def on_item_edited(self, item_text):
        """아이템이 수정되었을 때의 처리"""
        log_msg = f"수정된 로직: {item_text}"
        self.widget.log_message.emit(log_msg)
        
    def _handle_item_deleted(self, item_text):
        """아이템 삭제 처리"""
        self.on_item_deleted(item_text)
        
    def on_item_deleted(self, item_text):
        """아이템이 삭제되었을 때의 처리"""
        log_msg = f"삭제된 로직: {item_text}"
        self.widget.log_message.emit(log_msg)

    def _handle_logic_selected(self, logic_name):
        """로직이 선택되었을 때의 처리
        
        Args:
            logic_name (str): 선택된 로직의 이름
        """
        self.on_logic_selected(logic_name)
        
    def on_logic_selected(self, logic_name):
        """로직이 선택되었을 때의 처리
        
        Args:
            logic_name (str): 선택된 로직의 이름
        """
        pass  

    def on_logic_created(self, logic_name):
        """새로운 로직이 생성되었을 때의 처리
        
        Args:
            logic_name (str): 생성된 로직의 이름
        """
        # TODO: 새로운 로직을 리스트에 추가
        self.widget.list_widget.addItem(logic_name)

    def copy_logic(self, logic_data):
        """로직 복사"""
        new_logic = copy.deepcopy(logic_data)
        # ID는 원본 그대로 유지 (새로 생성하지 않음)
        
        # 중첩로직의 참조 관계도 그대로 유지
        if 'items' in new_logic:
            for item in new_logic['items']:
                if item['type'] == 'logic':
                    # 중첩로직의 logic_id와 참조 관계 유지
                    continue
                
        return new_logic

    def paste_logic(self, copied_logic):
        """로직 붙여넣기"""
        # 중첩로직 참조 검증
        if 'items' in copied_logic:
            for item in copied_logic['items']:
                if item['type'] == 'logic':
                    # 참조된 로직이 실제로 존재하는지 확인
                    referenced_logic = self.logic_manager.get_logic(item['logic_id'])
                    if not referenced_logic:
                        self.log_message.emit(f"[오류] 참조된 로직을 찾을 수 없습니다: {item['logic_name']}")
                        return None
        
        return copied_logic
