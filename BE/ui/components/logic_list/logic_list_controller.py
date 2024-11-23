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
        print("로직 순서가 변경되었습니다.")
        
    def _handle_item_edited(self, item_text):
        """아이템 수정 처리"""
        print(f"수정된 로직: {item_text}")
        
    def _handle_item_deleted(self, item_text):
        """아이템 삭제 처리"""
        print(f"삭제된 로직: {item_text}")

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
        pass  # 로그 출력 제거

    def on_logic_created(self, logic_name):
        """새로운 로직이 생성되었을 때의 처리
        
        Args:
            logic_name (str): 생성된 로직의 이름
        """
        # TODO: 새로운 로직을 리스트에 추가
        print(f"새로운 로직을 리스트에 추가: {logic_name}")
        self.widget.list_widget.addItem(logic_name)
