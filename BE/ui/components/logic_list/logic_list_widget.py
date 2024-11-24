from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...constants.styles import (FRAME_STYLE, LIST_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import LOGIC_LIST_WIDTH, BASIC_SECTION_HEIGHT, LOGIC_BUTTON_WIDTH

class LogicListWidget(QFrame):
    """로직 목록을 표시하고 관리하는 위젯"""
    
    # 시그널 정의
    item_moved = Signal()  # 아이템이 이동되었을 때
    item_edited = Signal(dict)  # 아이템이 수정되었을 때
    item_deleted = Signal(str)  # 아이템이 삭제되었을 때
    logic_selected = Signal(str)  # 로직이 선택되었을 때
    edit_logic = Signal(dict)  # 로직 수정 시그널 (로직 정보)
    log_message = Signal(str)  # 로그 메시지 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.saved_logics = {}  # 저장된 로직들을 관리하는 딕셔너리: {이름: 로직 정보}
        
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedSize(LOGIC_LIST_WIDTH, BASIC_SECTION_HEIGHT)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 타이틀
        title = QLabel("만든 로직 영역")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 리스트 위젯
        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_widget.setStyleSheet(LIST_STYLE)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.itemDoubleClicked.connect(self._item_double_clicked)
        layout.addWidget(self.list_widget)
        
        # 버튼 그룹 레이아웃
        button_group = QHBoxLayout()
        button_group.setContentsMargins(0, 0, 0, 0)
        button_group.setSpacing(5)
        
        # 버튼 생성
        self.up_btn = QPushButton("위로")
        self.down_btn = QPushButton("아래로")
        self.edit_btn = QPushButton("로직 수정")
        self.delete_btn = QPushButton("로직 삭제")
        
        # 버튼 설정
        for btn in [self.up_btn, self.down_btn, self.edit_btn, self.delete_btn]:
            btn.setFixedWidth(LOGIC_BUTTON_WIDTH)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setEnabled(False)
            button_group.addWidget(btn)
        
        layout.addLayout(button_group)
        self.setLayout(layout)
        
        # 버튼 시그널 연결
        self.up_btn.clicked.connect(self._move_item_up)
        self.down_btn.clicked.connect(self._move_item_down)
        self.edit_btn.clicked.connect(self._edit_item)
        self.delete_btn.clicked.connect(self._delete_item)
        
    def _on_selection_changed(self):
        """리스트 아이템 선택이 변경되었을 때의 처리"""
        has_selection = self.list_widget.currentRow() >= 0
        
        # 버튼 활성화/비활성화
        self.up_btn.setEnabled(has_selection and self.list_widget.currentRow() > 0)
        self.down_btn.setEnabled(has_selection and self.list_widget.currentRow() < self.list_widget.count() - 1)
        self.edit_btn.setEnabled(has_selection)
        self.delete_btn.setEnabled(has_selection)
        
        # 선택된 아이템이 있으면 시그널 발생
        if has_selection:
            self.logic_selected.emit(self.list_widget.currentItem().text())
            
    def _move_item_up(self):
        """현재 선택된 아이템을 위로 이동"""
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            current_item = self.list_widget.takeItem(current_row)
            self.list_widget.insertItem(current_row - 1, current_item)
            self.list_widget.setCurrentItem(current_item)
            self.item_moved.emit()
            
    def _move_item_down(self):
        """현재 선택된 아이템을 아래로 이동"""
        current_row = self.list_widget.currentRow()
        if current_row < self.list_widget.count() - 1:
            current_item = self.list_widget.takeItem(current_row)
            self.list_widget.insertItem(current_row + 1, current_item)
            self.list_widget.setCurrentItem(current_item)
            self.item_moved.emit()
            
    def on_logic_saved(self, logic_info):
        """로직이 저장되었을 때 호출되는 메서드"""
        name = logic_info['name']
        # 저장된 로직 정보 업데이트
        self.saved_logics[name] = logic_info
        
        # 리스트에 추가
        self.list_widget.addItem(QListWidgetItem(name))
        self.log_message.emit(f"로직 '{name}'이(가) 목록에 추가되었습니다")
        
    def on_logic_updated(self, original_name, logic_info):
        """로직이 수정되었을 때 호출되는 메서드"""
        # 저장된 로직 정보에서 원래 이름의 데이터를 삭제
        if original_name in self.saved_logics:
            del self.saved_logics[original_name]
        
        # 새 이름으로 로직 정보 저장
        name = logic_info['name']
        self.saved_logics[name] = logic_info
        
        # 리스트 위젯의 아이템 텍스트 업데이트
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.text() == original_name:
                item.setText(name)
                break
                
        self.log_message.emit(f"로직 '{name}'이(가) 업데이트되었습니다")
        
    def _item_double_clicked(self, item):
        """아이템이 더블클릭되었을 때 호출"""
        logic_name = item.text()
        if logic_name in self.saved_logics:
            logic_info = self.saved_logics[logic_name]
            self.log_message.emit(f"로직 데이터: {logic_info}")
            self.edit_logic.emit(logic_info)
            
    def _edit_item(self):
        """선택된 로직 수정"""
        current_item = self.list_widget.currentItem()
        if current_item:
            logic_name = current_item.text()
            if logic_name in self.saved_logics:
                logic_info = self.saved_logics[logic_name]
                self.edit_logic.emit(logic_info)
            
    def _delete_item(self):
        """선택된 아이템 삭제"""
        current_item = self.list_widget.currentItem()
        if current_item:
            logic_name = current_item.text()
            
            # 확인 모달 표시
            reply = QMessageBox.question(
                self,
                "로직 삭제",
                f"로직 '{logic_name}'을(를) 삭제하시겠습니까?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 저장된 로직 정보에서 삭제
                if logic_name in self.saved_logics:
                    del self.saved_logics[logic_name]
                
                # 리스트에서 삭제
                self.list_widget.takeItem(self.list_widget.row(current_item))
                self.log_message.emit(f"로직 '{logic_name}'이(가) 삭제되었습니다")
