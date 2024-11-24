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
    log_message = Signal(str)  # 로그 메시지 시그널
    logic_saved = Signal(str, list)  # 로직 저장 시그널 (이름, 아이템 리스트)
    logic_updated = Signal(str, list)  # 로직 수정 시그널 (이름, 아이템 리스트)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.edit_mode = False  # 수정 모드 여부
        
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
        
        # 버튼 그룹 레이아웃
        button_group = QHBoxLayout()
        button_group.setContentsMargins(0, 0, 0, 0)
        button_group.setSpacing(5)
        
        # 위로 버튼
        self.up_btn = QPushButton("위로")
        self.up_btn.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.up_btn.setStyleSheet(BUTTON_STYLE)
        self.up_btn.setEnabled(False)
        button_group.addWidget(self.up_btn)
        
        # 아래로 버튼
        self.down_btn = QPushButton("아래로")
        self.down_btn.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.down_btn.setStyleSheet(BUTTON_STYLE)
        self.down_btn.setEnabled(False)
        button_group.addWidget(self.down_btn)
        
        # 수정 버튼
        self.edit_btn = QPushButton("수정")
        self.edit_btn.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.edit_btn.setStyleSheet(BUTTON_STYLE)
        self.edit_btn.setEnabled(False)
        button_group.addWidget(self.edit_btn)
        
        # 삭제 버튼
        self.delete_btn = QPushButton("삭제")
        self.delete_btn.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.delete_btn.setStyleSheet(BUTTON_STYLE)
        self.delete_btn.setEnabled(False)
        button_group.addWidget(self.delete_btn)
        
        layout.addLayout(button_group)
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
        pass  # 더미 데이터 제거
            
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
        """로직 이름 저장 및 목록 전달"""
        logic_name = self.name_input.text().strip()
        if not logic_name:
            self.log_message.emit("로직 이름을 입력해주세요")
            return
            
        # 현재 목록의 모든 아이템을 리스트로 변환
        items = []
        for i in range(self.list_widget.count()):
            items.append(self.list_widget.item(i).text())
        
        if self.edit_mode:
            # 수정 모드일 경우 업데이트 시그널 발생
            self.logic_updated.emit(logic_name, items)
            self.edit_mode = False
        else:
            # 새로운 로직 저장
            self.logic_saved.emit(logic_name, items)
        
        # 저장 후 초기화
        self.name_input.clear()
        self.list_widget.clear()
        self.log_message.emit(f"로직 '{logic_name}'이(가) {'수정' if self.edit_mode else '저장'}되었습니다")

    def has_items(self):
        """목록에 아이템이 있는지 확인"""
        return self.list_widget.count() > 0

    def load_logic(self, name, items):
        """로직 데이터 로드"""
        self.edit_mode = True  # 수정 모드로 설정
        self.name_input.setText(name)
        self.name_input.setReadOnly(True)  # 이름 수정 불가
        self.list_widget.clear()
        for item in items:
            self.list_widget.addItem(QListWidgetItem(item))

    def add_item(self, item_text):
        """아이템 추가
        
        Args:
            item_text (str): 추가할 아이템의 텍스트
        """
        item = QListWidgetItem(item_text)
        self.list_widget.addItem(item)
        self.list_widget.setCurrentItem(item)
