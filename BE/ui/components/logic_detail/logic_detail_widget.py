from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QLineEdit)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...constants.styles import (FRAME_STYLE, LIST_STYLE, BUTTON_STYLE, CONTAINER_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import (LOGIC_DETAIL_WIDTH, BASIC_SECTION_HEIGHT,
                                 LOGIC_BUTTON_WIDTH)

class LogicDetailWidget(QFrame):
    """로직 상세 내용을 표시하고 관리하는 위젯"""
    
    # 시그널 정의
    item_moved = Signal()  # 아이템이 이동되었을 때
    item_edited = Signal(str)  # 아이템이 수정되었을 때
    item_deleted = Signal(str)  # 아이템이 삭제되었을 때
    logic_name_saved = Signal(str)  # 로직 이름이 저장되었을 때
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedSize(LOGIC_DETAIL_WIDTH, BASIC_SECTION_HEIGHT)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 타이틀
        title = QLabel("로직 구성 영역")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 로직 이름 레이아웃
        name_layout = QHBoxLayout()
        name_layout.setContentsMargins(0, 0, 0, 0)
        name_layout.setSpacing(5)
        
        # 로직 이름 라벨
        name_label = QLabel("로직 이름:")
        name_layout.addWidget(name_label)
        
        # 로직 이름 입력
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("로직의 이름을 입력하세요")
        name_layout.addWidget(self.name_input, 1)  # stretch factor 1을 주어 남은 공간을 채우도록
        
        # 저장 버튼
        self.save_btn = QPushButton("저장")
        self.save_btn.setStyleSheet(BUTTON_STYLE)
        self.save_btn.clicked.connect(self._save_logic_name)
        name_layout.addWidget(self.save_btn)
        
        layout.addLayout(name_layout)
        
        # 리스트 위젯
        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_widget.setStyleSheet(LIST_STYLE)
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.list_widget)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        
        # 버튼 생성
        self.up_btn = QPushButton("위로")
        self.down_btn = QPushButton("아래로")
        self.edit_btn = QPushButton("수정")
        self.delete_btn = QPushButton("삭제")
        
        # 버튼 설정
        for btn in [self.up_btn, self.down_btn, self.edit_btn, self.delete_btn]:
            btn.setFixedWidth(LOGIC_BUTTON_WIDTH)
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setEnabled(False)
            button_layout.addWidget(btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 버튼 시그널 연결
        self.up_btn.clicked.connect(self._move_item_up)
        self.down_btn.clicked.connect(self._move_item_down)
        self.edit_btn.clicked.connect(self._edit_item)
        self.delete_btn.clicked.connect(self._delete_item)
        
        # 초기 데이터 로드 (테스트용)
        self._load_test_data()
        
    def _load_test_data(self):
        """테스트용 데이터 로드"""
        for i in range(1, 7):
            item = QListWidgetItem(f"{i}. 키보드 A 입력")
            self.list_widget.addItem(item)
            
    def _on_selection_changed(self):
        """아이템 선택 상태 변경 시 호출"""
        has_selection = bool(self.list_widget.currentItem())
        for btn in [self.up_btn, self.down_btn, self.edit_btn, self.delete_btn]:
            btn.setEnabled(has_selection)
            
    def _move_item_up(self):
        """선택된 아이템을 위로 이동"""
        current_row = self.list_widget.currentRow()
        if current_row > 0:
            item = self.list_widget.takeItem(current_row)
            self.list_widget.insertItem(current_row - 1, item)
            self.list_widget.setCurrentItem(item)
            self.item_moved.emit()
            
    def _move_item_down(self):
        """선택된 아이템을 아래로 이동"""
        current_row = self.list_widget.currentRow()
        if current_row < self.list_widget.count() - 1:
            item = self.list_widget.takeItem(current_row)
            self.list_widget.insertItem(current_row + 1, item)
            self.list_widget.setCurrentItem(item)
            self.item_moved.emit()
            
    def _edit_item(self):
        """선택된 아이템 수정"""
        current_item = self.list_widget.currentItem()
        if current_item:
            self.item_edited.emit(current_item.text())
            
    def _delete_item(self):
        """선택된 아이템 삭제"""
        current_item = self.list_widget.currentItem()
        if current_item:
            row = self.list_widget.row(current_item)
            item = self.list_widget.takeItem(row)
            self.item_deleted.emit(item.text())

    def _save_logic_name(self):
        """로직 이름 저장"""
        name = self.name_input.text().strip()
        if name:
            self.logic_name_saved.emit(name)