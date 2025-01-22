from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QListWidgetItem)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from BE.function.constants.styles import (BUTTON_STYLE, LIST_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)

class LogicSelectorDialog(QDialog):
    """저장된 로직을 선택하는 다이얼로그"""
    
    logic_selected = Signal(str)  # 로직이 선택되었을 때 (로직 이름)
    
    def __init__(self, saved_logics, parent=None):
        super().__init__(parent)
        self.saved_logics = saved_logics
        self.selected_logic = None
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setWindowTitle("만든 로직 선택 모달")
        self.setMinimumWidth(500)
        self.setMinimumHeight(1300)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setSpacing(10)
        
        # 타이틀
        title = QLabel("저장된 로직 목록")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 리스트 위젯
        self.logic_list = QListWidget()
        self.logic_list.setStyleSheet(LIST_STYLE)
        self.logic_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        
        # 저장된 로직들을 리스트에 추가
        for logic_name, logic_info in self.saved_logics.items():
            display_text = logic_info.get('name', logic_name)  # 로직의 이름을 표시
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, logic_name)  # 로직 이름을 데이터로 저장
            self.logic_list.addItem(item)
            
        layout.addWidget(self.logic_list)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 추가 버튼
        add_btn = QPushButton("선택한 로직 추가")
        add_btn.setStyleSheet(BUTTON_STYLE)
        add_btn.clicked.connect(self._on_add_clicked)
        button_layout.addWidget(add_btn)
        
        # 취소 버튼
        cancel_btn = QPushButton("취소")
        cancel_btn.setStyleSheet(BUTTON_STYLE)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def _on_add_clicked(self):
        """추가 버튼 클릭 시"""
        current_item = self.logic_list.currentItem()
        if current_item:
            self.selected_logic = current_item.data(Qt.UserRole)  # 저장된 로직 이름 가져오기
            self.logic_selected.emit(self.selected_logic)
            self.accept()
            
    def _on_item_double_clicked(self, item):
        """아이템 더블 클릭 시"""
        self.selected_logic = item.data(Qt.UserRole)  # 저장된 로직 이름 가져오기
        self.logic_selected.emit(self.selected_logic)
        self.accept()
