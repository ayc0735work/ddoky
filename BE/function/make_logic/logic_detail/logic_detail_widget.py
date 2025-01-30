from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QLineEdit, QInputDialog, QMessageBox, QSpinBox, QCheckBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from BE.function.constants.styles import (FRAME_STYLE, LIST_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from BE.function.constants.dimensions import (LOGIC_DETAIL_WIDTH, BASIC_SECTION_HEIGHT,
                                 LOGIC_BUTTON_WIDTH)

class LogicDetailWidget(QFrame):
    """로직 상세 내용을 표시하고 관리하는 위젯"""
    
    # 시그널 정의
    item_moved = Signal()
    item_edited = Signal(str)
    item_deleted = Signal(str)
    logic_name_saved = Signal(str)

    def __init__(self, parent=None):
        """위젯 초기화"""
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedSize(LOGIC_DETAIL_WIDTH, BASIC_SECTION_HEIGHT)
        
        # 메인 레이아웃
        LogicConfigurationLayout__QVBoxLayout = QVBoxLayout()
        LogicConfigurationLayout__QVBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        LogicConfigurationLayout__QVBoxLayout.setContentsMargins(10, 10, 10, 10)
        LogicConfigurationLayout__QVBoxLayout.setSpacing(10)
        
        # 타이틀 레이아웃
        TitleRow__QHBoxLayout = QHBoxLayout()
        
        # 타이틀
        LogicTitleLabel__QLabel = QLabel("로직 상세 정보")
        LogicTitleLabel__QLabel.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        TitleRow__QHBoxLayout.addWidget(LogicTitleLabel__QLabel)
        
        TitleRow__QHBoxLayout.addStretch()
        LogicConfigurationLayout__QVBoxLayout.addLayout(TitleRow__QHBoxLayout)
        
        # 로직 저장 섹션
        LogicSaveSection__QHBoxLayout = QHBoxLayout()
        LogicSaveSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicSaveSection__QHBoxLayout.setSpacing(5)
        
        # 새 로직 버튼
        self.NewLogicButton__QPushButton = QPushButton("새 로직")
        self.NewLogicButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.NewLogicButton__QPushButton.setEnabled(False)  # 초기에 비활성화
        LogicSaveSection__QHBoxLayout.addWidget(self.NewLogicButton__QPushButton)
        
        # 로직 저장 버튼
        self.LogicSaveButton__QPushButton = QPushButton("로직 저장")
        self.LogicSaveButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        LogicSaveSection__QHBoxLayout.addWidget(self.LogicSaveButton__QPushButton)
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicSaveSection__QHBoxLayout)

        # 로직 이름 레이아웃
        LogicNameSection__QHBoxLayout = QHBoxLayout()
        LogicNameSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicNameSection__QHBoxLayout.setSpacing(5)
        
        # 로직 이름 라벨
        LogicNameLabel__QLabel = QLabel("로직 이름:")
        LogicNameLabel__QLabel.setFixedWidth(60)
        LogicNameSection__QHBoxLayout.addWidget(LogicNameLabel__QLabel)
        
        # 로직 이름 입력
        self.LogicNameInput__QLineEdit = QLineEdit()
        self.LogicNameInput__QLineEdit.setPlaceholderText("로직의 이름을 입력하세요")
        LogicNameSection__QHBoxLayout.addWidget(self.LogicNameInput__QLineEdit, 1)
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicNameSection__QHBoxLayout)

        # 트리거 키 입력 레이아웃
        TriggerKeySection__QHBoxLayout = QHBoxLayout()
        TriggerKeySection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        TriggerKeySection__QHBoxLayout.setSpacing(5)
        
        # 트리거 키 라벨
        TriggerKeyLabel__QLabel = QLabel("실행 트리거 키:")
        TriggerKeyLabel__QLabel.setFixedWidth(84)
        TriggerKeySection__QHBoxLayout.addWidget(TriggerKeyLabel__QLabel)
        
        # 트리거 키 입력 필드
        self.TriggerKeyInput__QLineEdit = QLineEdit()
        self.TriggerKeyInput__QLineEdit.setReadOnly(True)
        self.TriggerKeyInput__QLineEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        TriggerKeySection__QHBoxLayout.addWidget(self.TriggerKeyInput__QLineEdit)

        # 편집 버튼
        self.EditTriggerKeyButton__QPushButton = QPushButton("편집")
        self.EditTriggerKeyButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.EditTriggerKeyButton__QPushButton.setFixedWidth(40)
        self.EditTriggerKeyButton__QPushButton.setEnabled(False)  # 초기에는 비활성화
        TriggerKeySection__QHBoxLayout.addWidget(self.EditTriggerKeyButton__QPushButton)
        
        # 삭제 버튼
        self.DeleteTriggerKeyButton__QPushButton = QPushButton("삭제")
        self.DeleteTriggerKeyButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.DeleteTriggerKeyButton__QPushButton.setFixedWidth(40)
        self.DeleteTriggerKeyButton__QPushButton.setEnabled(False)  # 초기에는 비활성화
        TriggerKeySection__QHBoxLayout.addWidget(self.DeleteTriggerKeyButton__QPushButton)
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(TriggerKeySection__QHBoxLayout)
        
        # 기능 선택 레이아웃
        LogicOptionsSection__QHBoxLayout = QHBoxLayout()
        LogicOptionsSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicOptionsSection__QHBoxLayout.setSpacing(5)
        
        # 반복 횟수 입력 레이아웃
        RepeatCountRow__QHBoxLayout = QHBoxLayout()
        RepeatCountRow__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        RepeatCountRow__QHBoxLayout.setSpacing(5)
        
        # 반복 횟수 입력 필드
        self.RepeatCountInput__QSpinBox = QSpinBox()
        self.RepeatCountInput__QSpinBox.setFixedWidth(70)
        self.RepeatCountInput__QSpinBox.setAlignment(Qt.AlignRight)
        self.RepeatCountInput__QSpinBox.setRange(1, 9999)
        self.RepeatCountInput__QSpinBox.setValue(1)
        RepeatCountRow__QHBoxLayout.addWidget(self.RepeatCountInput__QSpinBox)
        
        # 반복 횟수 라벨
        RepeatCountLabel__QLabel = QLabel("회 반복")
        RepeatCountRow__QHBoxLayout.addWidget(RepeatCountLabel__QLabel)
        
        # 중첩로직용 체크박스 추가
        self.isNestedLogicCheckboxSelected_checkbox = QCheckBox("중첩로직용")
        RepeatCountRow__QHBoxLayout.addWidget(self.isNestedLogicCheckboxSelected_checkbox)
        
        RepeatCountRow__QHBoxLayout.addStretch()
        
        LogicOptionsSection__QHBoxLayout.addLayout(RepeatCountRow__QHBoxLayout)
        LogicOptionsSection__QHBoxLayout.addStretch()
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicOptionsSection__QHBoxLayout)
        
        # 리스트 위젯
        self.LogicItemList__QListWidget = QListWidget()
        self.LogicItemList__QListWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.LogicItemList__QListWidget.setStyleSheet(LIST_STYLE)
        self.LogicItemList__QListWidget.setSelectionMode(QListWidget.ExtendedSelection)  # 다중 선택 모드 활성화
        LogicConfigurationLayout__QVBoxLayout.addWidget(self.LogicItemList__QListWidget)
        
        # 버튼 그룹 레이아웃
        LogicControlButtonsSection__QHBoxLayout = QHBoxLayout()
        LogicControlButtonsSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicControlButtonsSection__QHBoxLayout.setSpacing(5)
        
        # 위로 버튼
        self.MoveUpButton__QPushButton = QPushButton("위로")
        self.MoveUpButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.MoveUpButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.MoveUpButton__QPushButton.setEnabled(False)
        LogicControlButtonsSection__QHBoxLayout.addWidget(self.MoveUpButton__QPushButton)
        
        # 아래로 버튼
        self.MoveDownButton__QPushButton = QPushButton("아래로")
        self.MoveDownButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.MoveDownButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.MoveDownButton__QPushButton.setEnabled(False)
        LogicControlButtonsSection__QHBoxLayout.addWidget(self.MoveDownButton__QPushButton)

        # 수정 버튼
        self.EditItemButton__QPushButton = QPushButton("항목 수정")
        self.EditItemButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.EditItemButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.EditItemButton__QPushButton.setEnabled(False)
        LogicControlButtonsSection__QHBoxLayout.addWidget(self.EditItemButton__QPushButton)

        # 삭제 버튼
        self.DeleteItemButton__QPushButton = QPushButton("항목 삭제")
        self.DeleteItemButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.DeleteItemButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.DeleteItemButton__QPushButton.setEnabled(False)
        LogicControlButtonsSection__QHBoxLayout.addWidget(self.DeleteItemButton__QPushButton)

        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicControlButtonsSection__QHBoxLayout)
        self.setLayout(LogicConfigurationLayout__QVBoxLayout)
        