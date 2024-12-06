from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QLineEdit, QInputDialog, QMessageBox, QSpinBox, QCheckBox)
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtGui import QFont, QGuiApplication, QIntValidator
from datetime import datetime
import uuid
import win32con
import win32api
from BE.settings.settings_manager import SettingsManager
from ...constants.styles import (FRAME_STYLE, LIST_STYLE, BUTTON_STYLE, CONTAINER_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import (LOGIC_DETAIL_WIDTH, BASIC_SECTION_HEIGHT,
                                 LOGIC_BUTTON_WIDTH)
from ....utils.key_handler import (KeyboardHook, get_key_display_text, get_key_location,
                                get_modifier_text, format_key_info)
from ..common.key_input_widget import KeyInputWidget

class LogicDetailWidget(QFrame):
    """로직 상세 내용을 표시하고 관리하는 위젯"""
    
    item_moved = Signal()
    item_edited = Signal(str)
    item_deleted = Signal(str)
    logic_name_saved = Signal(str)
    log_message = Signal(str)
    logic_saved = Signal(dict)
    logic_updated = Signal(str, dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.edit_mode = False  # 수정 모드 여부
        self.last_key_info = None
        self.keyboard_hook = None
        self.trigger_key_info = None  # 트리거 키 정보
        self.original_name = None  # 원래 이름
        self.current_logic_id = None  # 현재 로직의 UUID 저장용 추가
        self.copied_items = []  # 복사된 아이템들 저장 (리스트로 변경)
        self.current_logic = None  # 현재 로직 정보
        self.settings_manager = SettingsManager()  # SettingsManager 인스턴스 생성
        
        # 키보드 이벤트 필터 설치
        self.installEventFilter(self)
        
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
        LogicTitleLabel__QLabel = QLabel("로직 구성 영역")
        LogicTitleLabel__QLabel.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        TitleRow__QHBoxLayout.addWidget(LogicTitleLabel__QLabel)
        
        TitleRow__QHBoxLayout.addStretch()
        LogicConfigurationLayout__QVBoxLayout.addLayout(TitleRow__QHBoxLayout)
        
        # 로직 이름 레이아웃
        LogicNameSection__QHBoxLayout = QHBoxLayout()
        LogicNameSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicNameSection__QHBoxLayout.setSpacing(5)
        
        # 로직 이름 라벨
        LogicNameLabel__QLabel = QLabel("로직 이름:")
        LogicNameLabel__QLabel.setFixedWidth(70)
        LogicNameSection__QHBoxLayout.addWidget(LogicNameLabel__QLabel)
        
        # 로직 이름 입력
        self.LogicNameInput__QLineEdit = QLineEdit()
        self.LogicNameInput__QLineEdit.setPlaceholderText("로직의 이름을 입력하세요")
        self.LogicNameInput__QLineEdit.textChanged.connect(self._check_data_entered)  # 텍스트 변경 시그널 연결
        LogicNameSection__QHBoxLayout.addWidget(self.LogicNameInput__QLineEdit, 1)  # stretch factor 1을 추가하여 남은 공간을 모 사용
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicNameSection__QHBoxLayout)
        
        # 로직 저장 섹션
        LogicSaveSection__QHBoxLayout = QHBoxLayout()
        LogicSaveSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicSaveSection__QHBoxLayout.setSpacing(5)
        
        # 새 로직 버튼
        self.NewLogicButton__QPushButton = QPushButton("새 로직")
        self.NewLogicButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.NewLogicButton__QPushButton.clicked.connect(self._create_new_logic)
        self.NewLogicButton__QPushButton.setEnabled(False)  # 초기에는 비활성화
        LogicSaveSection__QHBoxLayout.addWidget(self.NewLogicButton__QPushButton)
        
        # 로직 저장 버튼
        self.LogicSaveButton__QPushButton = QPushButton("로직 저장")
        self.LogicSaveButton__QPushButton.setStyleSheet(BUTTON_STYLE)
        self.LogicSaveButton__QPushButton.clicked.connect(self._save_logic)
        LogicSaveSection__QHBoxLayout.addWidget(self.LogicSaveButton__QPushButton)
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicSaveSection__QHBoxLayout)
        
        # 트리거 키 정보 영역
        TriggerKeySection__QVBoxLayout = QVBoxLayout()
        TriggerKeySection__QVBoxLayout.setContentsMargins(0, 0, 0, 0)
        TriggerKeySection__QVBoxLayout.setSpacing(5)
        
        # 트리거 키 입력 레이아웃
        TriggerKeyInputRow__QHBoxLayout = QHBoxLayout()
        TriggerKeyInputRow__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        TriggerKeyInputRow__QHBoxLayout.setSpacing(5)
        
        # 트리거 키 입력 라벨
        TriggerKeyLabel__QLabel = QLabel("트리거 키:")
        TriggerKeyLabel__QLabel.setFixedWidth(70)
        TriggerKeyInputRow__QHBoxLayout.addWidget(TriggerKeyLabel__QLabel)
        
        # 트리거 키 입력 위젯
        self.TriggerKeyInputWidget__KeyInputWidget = KeyInputWidget(self, show_details=False)
        self.TriggerKeyInputWidget__KeyInputWidget.key_input_changed.connect(self._on_key_input_changed)
        self.TriggerKeyInputWidget__KeyInputWidget.key_input_changed.connect(self._check_data_entered)  # 키 입력 변경 시그널 연결
        TriggerKeyInputRow__QHBoxLayout.addWidget(self.TriggerKeyInputWidget__KeyInputWidget)
        
        TriggerKeySection__QVBoxLayout.addLayout(TriggerKeyInputRow__QHBoxLayout)
        
        # 트리거 키 정보 라벨
        self.TriggerKeyInfoLabel__QLabel = QLabel()
        self.TriggerKeyInfoLabel__QLabel.setStyleSheet(CONTAINER_STYLE)
        self.TriggerKeyInfoLabel__QLabel.mousePressEvent = self._copy_key_info_to_clipboard
        TriggerKeySection__QVBoxLayout.addWidget(self.TriggerKeyInfoLabel__QLabel)
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(TriggerKeySection__QVBoxLayout)
        
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
        self.RepeatCountInput__QSpinBox.valueChanged.connect(self._check_data_entered)
        RepeatCountRow__QHBoxLayout.addWidget(self.RepeatCountInput__QSpinBox)
        
        # 반복 횟수 라벨
        RepeatCountLabel__QLabel = QLabel("회 반복")
        RepeatCountRow__QHBoxLayout.addWidget(RepeatCountLabel__QLabel)
        
        # 중첩로직용 체크박스 추가
        self.is_nested_checkbox = QCheckBox("중첩로직용")
        self.is_nested_checkbox.stateChanged.connect(self._on_nested_checkbox_changed)
        RepeatCountRow__QHBoxLayout.addWidget(self.is_nested_checkbox)
        
        RepeatCountRow__QHBoxLayout.addStretch()
        
        LogicOptionsSection__QHBoxLayout.addLayout(RepeatCountRow__QHBoxLayout)
        LogicOptionsSection__QHBoxLayout.addStretch()
        
        LogicConfigurationLayout__QVBoxLayout.addLayout(LogicOptionsSection__QHBoxLayout)
        
        # 리스트 위젯
        self.LogicItemList__QListWidget = QListWidget()
        self.LogicItemList__QListWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.LogicItemList__QListWidget.setStyleSheet(LIST_STYLE)
        self.LogicItemList__QListWidget.setSelectionMode(QListWidget.ExtendedSelection)  # 다중 선택 모드 활성화
        self.LogicItemList__QListWidget.itemSelectionChanged.connect(self._on_selection_changed)
        self.LogicItemList__QListWidget.itemDoubleClicked.connect(self._edit_item)  # 더블클릭 시그널 연결
        # 아이템 목록 변경 시 새 로직 버튼 상태 업데이트
        self.LogicItemList__QListWidget.model().rowsInserted.connect(self._check_data_entered)
        self.LogicItemList__QListWidget.model().rowsRemoved.connect(self._check_data_entered)
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
        
        # 버튼 시그널 연결
        self.MoveUpButton__QPushButton.clicked.connect(self._move_item_up)
        self.MoveDownButton__QPushButton.clicked.connect(self._move_item_down)
        self.EditItemButton__QPushButton.clicked.connect(self._edit_item)
        self.DeleteItemButton__QPushButton.clicked.connect(self._delete_item)
        
        # 초기 데이터 로드 (테스트용)
        self._load_test_data()
        
    def _load_test_data(self):
        """테스트용 데이터 로드"""
        pass  # 더미 데이터 제거
            
    def _on_selection_changed(self):
        """리스트 아이템 선택이 변경되었을 때의 처리"""
        selected_items = self.LogicItemList__QListWidget.selectedItems()
        has_selection = len(selected_items) > 0
        
        # 버튼 활성화/비활성화
        current_row = self.LogicItemList__QListWidget.currentRow()
        self.MoveUpButton__QPushButton.setEnabled(has_selection and current_row > 0)
        self.MoveDownButton__QPushButton.setEnabled(has_selection and current_row < self.LogicItemList__QListWidget.count() - 1)
        self.EditItemButton__QPushButton.setEnabled(len(selected_items) == 1)  # 수정은 단일 선택만 가능
        self.DeleteItemButton__QPushButton.setEnabled(has_selection)  # 삭제는 다중 선택 가능

    def add_item(self, item_text):
        """아이템 추가
        
        Args:
            item_text (str): 추가할 아이템의 텍스트
        """
        item = QListWidgetItem(item_text)
        current_row = self.LogicItemList__QListWidget.currentRow()
        
        # 선택된 아이템이 없거나 마지막 아이템인 경우 마지막에 추가
        if current_row < 0:
            insert_position = self.LogicItemList__QListWidget.count()
        else:
            insert_position = current_row + 1
            
        # order 값 업데이트
        for i in range(insert_position, self.LogicItemList__QListWidget.count()):
            existing_item = self.LogicItemList__QListWidget.item(i)
            if existing_item:
                existing_data = existing_item.data(Qt.UserRole) or {}
                existing_data['order'] = i + 2  # 새 아이템이 들어갈 자리 이후의 아이템들의 order 증가
                existing_item.setData(Qt.UserRole, existing_data)
        
        # 새 아이템의 order 설정
        item.setData(Qt.UserRole, {'order': insert_position + 1, 'content': item_text})
        
        # 기존 선택 해제
        for i in range(self.LogicItemList__QListWidget.count()):
            self.LogicItemList__QListWidget.item(i).setSelected(False)
            
        # 새 아이템 추가 및 선택
        self.LogicItemList__QListWidget.insertItem(insert_position, item)
        self.LogicItemList__QListWidget.setCurrentItem(item)

    def _move_item_up(self):
        """현재 선택된 아이템을 위로 이동"""
        current_row = self.LogicItemList__QListWidget.currentRow()
        if current_row > 0:
            current_item = self.LogicItemList__QListWidget.takeItem(current_row)
            # 아이템 이동 시 order 값 업데이트
            prev_item = self.LogicItemList__QListWidget.item(current_row - 1)
            current_data = current_item.data(Qt.UserRole) or {}
            prev_data = prev_item.data(Qt.UserRole) or {}
            current_data['order'], prev_data['order'] = prev_data.get('order', current_row), current_data.get('order', current_row + 1)
            current_item.setData(Qt.UserRole, current_data)
            prev_item.setData(Qt.UserRole, prev_data)
            self.LogicItemList__QListWidget.insertItem(current_row - 1, current_item)
            self.LogicItemList__QListWidget.setCurrentItem(current_item)
            self.item_moved.emit()

    def _move_item_down(self):
        """현재 선택된 아이템을 아래로 이동"""
        current_row = self.LogicItemList__QListWidget.currentRow()
        if current_row < self.LogicItemList__QListWidget.count() - 1:
            current_item = self.LogicItemList__QListWidget.takeItem(current_row)
            # 아이템 이동 시 order 값 업데이트
            next_item = self.LogicItemList__QListWidget.item(current_row)
            current_data = current_item.data(Qt.UserRole) or {}
            next_data = next_item.data(Qt.UserRole) or {}
            current_data['order'], next_data['order'] = next_data.get('order', current_row + 2), current_data.get('order', current_row + 1)
            current_item.setData(Qt.UserRole, current_data)
            next_item.setData(Qt.UserRole, next_data)
            self.LogicItemList__QListWidget.insertItem(current_row + 1, current_item)
            self.LogicItemList__QListWidget.setCurrentItem(current_item)
            self.item_moved.emit()

    def get_items(self):
        """현재 로직의 아이템 목록을 반환"""
        items = []
        logics = self.settings_manager.load_logics()  # 모든 로직 정보 로드
        
        for i in range(self.LogicItemList__QListWidget.count()):
            item = self.LogicItemList__QListWidget.item(i)
            item_text = item.text()
            user_data = item.data(Qt.UserRole) or {}
            order = user_data.get('order', i + 1)
            
            # 로직 타입 아이템인 경우
            if item_text.startswith("로직:") or not any(item_text.startswith(prefix) for prefix in ["키 입력:", "지연시간"]):
                logic_data = user_data.get('logic_data', {})
                logic_name = logic_data.get('logic_name') or item_text.replace("로직:", "").strip()
                
                # 기존 로직의 UUID를 우선적으로 사용
                logic_id = logic_data.get('logic_id')
                
                # UUID가 없거나 유효하지 않은 경우
                if not logic_id or logic_id not in logics:
                    # 이름이 일치하는 모든 로직 찾기
                    matching_logics = [(id, logic) for id, logic in logics.items() 
                                     if logic.get('name') == logic_name]
                    
                    if matching_logics:
                        # 가장 오래된 로직의 UUID 사용
                        matching_logics.sort(key=lambda x: x[1].get('created_at', ''))
                        logic_id = matching_logics[0][0]
                        
                        # 다른 모든 일치하는 로직들도 같은 UUID로 업데이트
                        for other_id, other_logic in logics.items():
                            if other_logic.get('name') == logic_name:
                                other_logic['id'] = logic_id
                                self.settings_manager.save_logic(other_id, other_logic)
                    else:
                        # 일치하는 로직이 없는 경우 새 UUID 생성
                        logic_id = str(uuid.uuid4())

                repeat_count = logic_data.get('repeat_count', 1)
                items.append({
                    'type': 'logic',
                    'logic_id': logic_id,
                    'logic_name': logic_name,
                    'repeat_count': repeat_count,
                    'display_text': item_text,
                    'order': order,
                    'logic_data': {
                        'logic_id': logic_id,
                        'logic_name': logic_name,
                        'repeat_count': repeat_count
                    }
                })
            # 키 입력 아이템인 경우
            elif item_text.startswith("키 입력:"):
                key_parts = item_text.split(" --- ")
                if len(key_parts) == 2:
                    key_text = key_parts[0].replace("키 입력: ", "").strip()
                    action = key_parts[1]  # "누르기" 또는 "떼기"
                    
                    # 수정자 키가 있는지 확인
                    if "+" in key_text:
                        modifiers_text, key = key_text.rsplit("+", 1)
                        modifiers = modifiers_text.strip()
                    else:
                        modifiers = "없음"
                        key = key_text
                    
                    key = key.strip()
                    
                    # 가상 키 코드와 스캔 코드 가져오기
                    import win32con
                    import win32api
                    
                    # 키 코드 매핑
                    key_code_map = {
                        '왼쪽 쉬프트': win32con.VK_LSHIFT,
                        '오른쪽 쉬프트': win32con.VK_RSHIFT,
                        '왼쪽 컨트롤': win32con.VK_LCONTROL,
                        '오른쪽 컨트롤': win32con.VK_RCONTROL,
                        '왼쪽 알트': win32con.VK_LMENU,
                        '오른쪽 알트': win32con.VK_RMENU,
                        'Home': win32con.VK_HOME,
                        '엔터': win32con.VK_RETURN,
                        '숫자패드 엔터': win32con.VK_RETURN,  # 일반 엔터와 같은 가상 키 코드 사용
                        'Tab': win32con.VK_TAB,
                        'ESC': win32con.VK_ESCAPE,
                        'Space': win32con.VK_SPACE,
                        'Backspace': win32con.VK_BACK,
                        'Delete': win32con.VK_DELETE,
                        'Insert': win32con.VK_INSERT,
                        'End': win32con.VK_END,
                        'Page Up': win32con.VK_PRIOR,
                        'Page Down': win32con.VK_NEXT,
                        '방향키 왼쪽 ←': win32con.VK_LEFT,
                        '방향키 오른쪽 →': win32con.VK_RIGHT,
                        '방향키 위쪽 ↑': win32con.VK_UP,
                        '방키 아래쪽 ↓': win32con.VK_DOWN,
                        '숫자패드 0': win32con.VK_NUMPAD0,
                        '숫자패드 1': win32con.VK_NUMPAD1,
                        '숫자패드 2': win32con.VK_NUMPAD2,
                        '숫자패드 3': win32con.VK_NUMPAD3,
                        '숫자패드 4': win32con.VK_NUMPAD4,
                        '숫자패드 5': win32con.VK_NUMPAD5,
                        '숫자패드 6': win32con.VK_NUMPAD6,
                        '숫자패드 7': win32con.VK_NUMPAD7,
                        '숫자패드 8': win32con.VK_NUMPAD8,
                        '숫자패드 9': win32con.VK_NUMPAD9,
                        '숫자패드 *': win32con.VK_MULTIPLY,
                        '숫자패드 +': win32con.VK_ADD,
                        '숫자패드 -': win32con.VK_SUBTRACT,
                        '숫자패드 .': win32con.VK_DECIMAL,
                        '숫자패드 /': win32con.VK_DIVIDE,
                    }
                    
                    # 가상 키 코드 얻기
                    if key in key_code_map:
                        virtual_key = key_code_map[key]
                    else:
                        # 일반 문자키인 경우
                        if len(key) == 1:
                            virtual_key = ord(key.upper())
                        else:
                            virtual_key = 0  # 알 수 없는 키
                    
                    # 스캔 코드 얻기
                    if key == '숫자패드 엔터':
                        scan_code = 0x1C + 0xE0  # 252 (숫자패드 엔터의 확장 스캔 코드)
                    else:
                        scan_code = win32api.MapVirtualKey(virtual_key, 0)
                    
                    # 수정자 키를 정수값으로 매핑
                    modifier_map = {
                        'Shift': 0x02000000,  # Qt.ShiftModifier 값
                        'Ctrl': 0x04000000,   # Qt.ControlModifier 값
                        'Alt': 0x08000000,    # Qt.AltModifier 값
                    }
                    
                    modifier_value = 0
                    if modifiers != "없음":
                        for mod in modifiers.split('+'):
                            mod = mod.strip()
                            if mod in modifier_map:
                                modifier_value |= modifier_map[mod]
                    
                    # 구조화된 형태로 저장
                    item_data = {
                        "type": "key_input",
                        "key_code": key,
                        "scan_code": scan_code,
                        "virtual_key": virtual_key,
                        "modifiers": modifier_value,
                        "action": action,
                        "display_text": item_text,
                        "order": order
                    }
                    items.append(item_data)
                else:
                    items.append({"type": "text", "content": item_text, "order": order})
            # 지연시간 아이템인 경우
            elif item_text.startswith("지연시간"):
                items.append({
                    "type": "delay",
                    "duration": float(item_text.split(":")[1].replace("초", "").strip()),
                    "display_text": item_text,
                    "order": order
                })
            # 기타 아이템
            else:
                # 반 텍스트 아이템을 로직 타입으로 변환
                items.append({
                    'type': 'logic',
                    'logic_name': item_text,
                    'display_text': f"로직: {item_text}",
                    'logic_id': str(uuid.uuid4()),  # 새로운 UUID 생성
                    'repeat_count': 1,
                    'order': order
                })
        
        # order 값으로 정렬
        return sorted(items, key=lambda x: x.get('order', float('inf')))

    def clear_all(self):
        """모든 입력과 상태를 초기화"""
        self.LogicNameInput__QLineEdit.clear()           # 로직 이름 초기화
        self.LogicItemList__QListWidget.clear()          # 목록 초기화
        self.TriggerKeyInputWidget__KeyInputWidget.clear_key()        # 트리거 키 입력 초기화
        self.TriggerKeyInfoLabel__QLabel.clear()       # 트리거 키 정보 초기화
        self.trigger_key_info = None      # 트리 키 정보 초기화
        self.edit_mode = False            # 수정 모드 해제
        self.original_name = None         # 원래 이름 초기화
        self.current_logic_id = None     # UUID도 초기화
        self.RepeatCountInput__QSpinBox.setValue(1)    # 반복 횟수를 기본값(1)으로 기화
        self.current_logic = None         # 현재 로직 정보 초기화
        self.copied_items = []            # 복사된 아이템 초기화
        self.is_nested_checkbox.setChecked(False)      # 중첩로직용 체크박스 초기화

    def _on_key_input_changed(self, key_info):
        """키 입력이 변경되었을 때"""
        if not key_info:  # 키 정보가 비어있으면 라벨 초기화
            self.TriggerKeyInfoLabel__QLabel.clear()
            return
            
        # modifiers가 이미 정수값인지 확인하고, 아니라면 int() 변환을 건너뜁니다
        if not isinstance(key_info['modifiers'], int):
            key_info['modifiers'] = key_info['modifiers'].value
            
        self.TriggerKeyInfoLabel__QLabel.setText(format_key_info(key_info))
        self.trigger_key_info = key_info  # 트리거 키 정보 저장

    def _save_logic(self):
        """로직 저장"""
        try:
            # 로직 이름 가져오
            name = self.LogicNameInput__QLineEdit.text().strip()
            if not name:
                self.log_message.emit("오류: 로직 이름을 입력해주세요.")
                return False

            # 중첩로직용 여부 확인
            is_nested = self.is_nested_checkbox.isChecked()

            # 중첩로직용이 아닐 경우에만 트리거 키 검사
            if not is_nested and not self.trigger_key_info:
                self.log_message.emit("오류: 트리거 키를 설정해주세요.")
                return False

            # 아이템 존재 여부 확인
            if not self.has_items():
                self.log_message.emit("오류: 로직에 아이템을 추가해주세요.")
                return False

            # get_items 메서드를 사용하여 아이템 정보 가져오기
            items = self.get_items()

            # 현재 로직 정보 구성
            logic_info = {
                'name': name,
                'order': self.current_logic.get('order', 0) if self.current_logic else 0,
                'created_at': datetime.now().isoformat() if not self.current_logic else self.current_logic.get('created_at'),
                'updated_at': datetime.now().isoformat(),
                'repeat_count': self.RepeatCountInput__QSpinBox.value(),
                'items': items,
                'is_nested': is_nested,  # 중첩로직용 여부 저장
                'trigger_key': {         # 중첩로직용일 때는 빈 트리거 키 정보 저장
                    'display_text': '',
                    'key_code': '',
                    'modifiers': 0,
                    'scan_code': 0,
                    'virtual_key': 0
                }
            }

            # 중첩로직용이 아닐 경우에만 실제 트리거 키 정보로 업데이트
            if not is_nested and self.trigger_key_info:
                logic_info['trigger_key'] = {
                    'display_text': self.trigger_key_info.get('display_text', ''),
                    'key_code': self.trigger_key_info.get('key_code', ''),
                    'modifiers': self.trigger_key_info.get('modifiers', 0),
                    'scan_code': self.trigger_key_info.get('scan_code', 0),
                    'virtual_key': self.trigger_key_info.get('virtual_key', 0)
                }

            # 수정 모드인 경우 업데이트
            if self.current_logic and self.current_logic_id:  # UUID가 있는 경우
                # UUID로 저장
                self.settings_manager.save_logic(self.current_logic_id, logic_info)
                self.logic_updated.emit(self.original_name, logic_info)
                self.log_message.emit(f"로직 '{name}'이(가) 업데이트되었습니다.")
            else:
                # 새 로직 저장
                new_logic_id = str(uuid.uuid4())
                self.settings_manager.save_logic(new_logic_id, logic_info)
                self.logic_saved.emit(logic_info)
                self.log_message.emit(f"새 로직 '{name}'이(가) 저장되었습니다.")

            # 저장 후 입력 초기화
            self.clear_all()
            return True

        except Exception as e:
            self.log_message.emit(f"로직 저장 중 오류 발생: {str(e)}")
            return False

    def load_logic(self, logic_info):
        """로직 정보를 위젯에 로드"""
        try:
            if not logic_info or not isinstance(logic_info, dict):
                self.log_message.emit("오류: 잘못된 로직 정보입니다.")
                return

            # UI 초기화
            self.clear_all()
            
            # 기본 정보 설정
            self.LogicNameInput__QLineEdit.setText(logic_info.get('name', ''))
            self.current_logic = logic_info.copy()
            self.edit_mode = True
            self.original_name = logic_info.get('name')
            
            # UUID 저장 (logic_info에서 직접 가져옴)
            self.current_logic_id = logic_info.get('id')
            
            # 중첩로직 여부 설정 (먼저 설정하여 트리거 키 UI 상태 제어)
            is_nested = logic_info.get('is_nested', False)
            self.is_nested_checkbox.setChecked(is_nested)
            
            # 중첩로직이 아닐 경우에만 트리거 키 설정
            if not is_nested:
                trigger_key = logic_info.get('trigger_key', {})
                if isinstance(trigger_key, dict) and trigger_key:
                    self.trigger_key_info = trigger_key.copy()
                    self.TriggerKeyInfoLabel__QLabel.setText(format_key_info(trigger_key))
                    self.TriggerKeyInputWidget__KeyInputWidget.set_key_info(trigger_key)
            
            # 반복 횟수 설정
            repeat_count = logic_info.get('repeat_count', 1)
            self.RepeatCountInput__QSpinBox.setValue(repeat_count)
            
            # 로직 아이템 목록 설정
            items = logic_info.get('items', [])
            if isinstance(items, list):
                sorted_items = sorted(items, key=lambda x: x.get('order', float('inf')))
                for item in sorted_items:
                    if isinstance(item, dict):
                        if item.get('type') == 'delay':
                            display_text = f"지연시간 : {item.get('duration', 0.0)}초"
                            item['display_text'] = display_text
                        elif item.get('type') == 'logic':
                            logic_name = item.get('logic_name', '')
                            display_text = f"{logic_name}"
                            item['display_text'] = display_text
                        self._add_logic_item(item)
            
            self.log_message.emit(f"로직 '{logic_info.get('name')}'이(가) 로드되었습니다.")

        except Exception as e:
            self.log_message.emit(f"로직 로드 중 오류 발생: {str(e)}")
            self.clear_all()

    def _add_logic_item(self, item_info):
        """로직 아이템을 리스트에 추가"""
        if not isinstance(item_info, dict):
            return
            
        # 이미 변환된 형식인 경우 (로직 타입)
        if item_info.get('type') == 'logic':
            logic_name = item_info.get('logic_name')
            logic_id = item_info.get('logic_id')
            
            # UUID가 없거나 유효하지 않은 경우
            if not logic_id or logic_id not in self.settings_manager.load_logics():
                # 이름으로 찾기
                logics = self.settings_manager.load_logics()
                for existing_id, existing_logic in logics.items():
                    if existing_logic.get('name') == logic_name:
                        logic_id = existing_id
                        break
                
                # 여전히 찾지 못한 경우
                if not logic_id:
                    QMessageBox.critical(
                        self,
                        "오류",
                        f"원본 로직 '{logic_name}'을(를) 찾을 수 없습니다.\n"
                        "해당 로직이 삭제되었거나 이름이 변경되었을 수 있습니다."
                    )
                    return
                
                # UUID 업데이트
                item_info['logic_id'] = logic_id
                if 'logic_data' in item_info:
                    item_info['logic_data']['logic_id'] = logic_id
            
            self.log_message.emit(f"중첩 로직 '{logic_name}'의 UUID가 {logic_id}로 업데이트되었습니다.")
        
        # content 필드가 있는 경우 (이전 형식) 새 형식으로 변환
        elif 'content' in item_info:
            content = item_info['content']
            if "키 입력:" in content:
                # 키 입력 아이템 처리...
                pass
            else:
                # 로직 이름으로 원본 로직 찾기
                logic_name = content.replace("로직:", "").strip()
                logics = self.settings_manager.load_logics()
                logic_id = None
                
                # 이름으로 원본 로직 찾기
                for existing_id, existing_logic in logics.items():
                    if existing_logic.get('name') == logic_name:
                        logic_id = existing_id
                        break
                
                # 원본 로직을 찾지 못한 경우 에러 메시지 표시
                if not logic_id:
                    QMessageBox.critical(
                        self,
                        "오류",
                        f"원본 로직 '{logic_name}'을(를) 찾을 수 없습니다.\n"
                        "해당 로직이 삭제되었거나 이름이 변경되었을 수 있습니다."
                    )
                    return
                
                item_info = {
                    'type': 'logic',
                    'logic_name': logic_name,
                    'display_text': f"로직: {logic_name}",
                    'logic_id': logic_id,
                    'repeat_count': 1,
                    'order': item_info.get('order', 1),
                    'logic_data': {
                        'logic_id': logic_id,
                        'logic_name': logic_name,
                        'repeat_count': 1
                    }
                }
        
        # 아이템의 순서를 현재 리스트의 아이템 개수 + 1로 설정
        current_count = self.LogicItemList__QListWidget.count()
        item_info['order'] = current_count + 1
        
        # QListWidgetItem 생성 및 추가
        item = QListWidgetItem(item_info.get('display_text', ''))
        item.setData(Qt.UserRole, item_info)
        self.LogicItemList__QListWidget.addItem(item)

    def has_items(self):
        """목록에 아이템이 있는지 확인"""
        return self.LogicItemList__QListWidget.count() > 0

    def _copy_key_info_to_clipboard(self, event):
        """트리거 키 정보를 클립보드에 복사"""
        if self.TriggerKeyInfoLabel__QLabel.text():
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.TriggerKeyInfoLabel__QLabel.text())
            self.log_message.emit("트리거 키 정보가 클립보드에 복사되었습니다")

    def _copy_item(self):
        """선택된 아이템들을 복사"""
        selected_items = self.LogicItemList__QListWidget.selectedItems()
        if selected_items:
            self.copied_items = [item.text() for item in selected_items]
            items_count = len(self.copied_items)
            self.log_message.emit(f"{items_count}개의 로직 구성 아이템이 복사되었습니다")
            
    def _paste_item(self):
        """복사된 아이템들을 현재 선택된 아이템 아래에 붙여넣기"""
        if not self.copied_items:
            self.log_message.emit("복사된 아이템이 없습니다")
            return
            
        current_row = self.LogicItemList__QListWidget.currentRow()
        if current_row < 0:
            insert_position = self.LogicItemList__QListWidget.count()
        else:
            insert_position = current_row + 1
            
        # 복사된 아이템들을 선택된 아이템 바로 다음에 순서대로 추가
        for idx, item_text in enumerate(self.copied_items):
            current_insert_position = insert_position + idx
            
            # 중첩 로직인 경우 원본 로직의 UUID 찾기
            if item_text.startswith("로직:"):
                logic_name = item_text.replace("로직:", "").strip()
                
                # settings.json에서 이름으로 원본 로직 찾기
                logics = self.settings_manager.load_logics()
                logic_id = None
                
                # 이름이 일치하는 로직 찾기
                for existing_id, existing_logic in logics.items():
                    if existing_logic.get('name') == logic_name:
                        logic_id = existing_id
                        break
                
                if not logic_id:
                    QMessageBox.critical(
                        self,
                        "오류",
                        f"원본 로직 '{logic_name}'을(를) 찾을 수 없습니다.\n"
                        "해당 로직이 삭제되었거나 이름이 변경되었을 수 있습니다."
                    )
                    continue
                
                # 새 아이템 생성 시 찾은 UUID 사용
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, {
                    'order': current_insert_position + 1,
                    'content': item_text,
                    'logic_data': {
                        'logic_id': logic_id,  # 찾은 UUID 사용
                        'logic_name': logic_name,
                        'repeat_count': 1
                    }
                })
            else:
                # 일반 아이템의 경우 기존 처리 유지
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, {
                    'order': current_insert_position + 1, 
                    'content': item_text
                })
            
            # 뒤의 아이템들의 order 업데이트
            for i in range(current_insert_position, self.LogicItemList__QListWidget.count()):
                existing_item = self.LogicItemList__QListWidget.item(i)
                if existing_item:
                    existing_data = existing_item.data(Qt.UserRole) or {}
                    existing_data['order'] = i + 2
                    existing_item.setData(Qt.UserRole, existing_data)
            
            self.LogicItemList__QListWidget.insertItem(current_insert_position, item)
        
        # 마지막으로 붙여넣은 아이템 선택
        last_inserted_item = self.LogicItemList__QListWidget.item(insert_position + len(self.copied_items) - 1)
        if last_inserted_item:
            self.LogicItemList__QListWidget.setCurrentItem(last_inserted_item)
            
        items_count = len(self.copied_items)
        self.log_message.emit(f"{items_count}개의 로직 구성 아이템이 붙여넣기되었습니다")

    def eventFilter(self, obj, event):
        """이벤트 필터"""
        if event.type() == QEvent.KeyPress:
            modifiers = event.modifiers()
            key = event.key()
            
            # Ctrl+C: 복사
            if modifiers == Qt.ControlModifier and key == Qt.Key_C:
                self._copy_item()
                return True
                
            # Ctrl+V: 붙여넣기
            elif modifiers == Qt.ControlModifier and key == Qt.Key_V:
                self._paste_item()
                return True
                
            # Delete: 삭제
            elif key == Qt.Key_Delete:
                self._delete_item()
                return True
                
        return super().eventFilter(obj, event)

    def _check_data_entered(self, *args):
        """입력된 데이터가 있는지 확인하고 새 로직 버튼 상태를 업데이트"""
        # 새 로직 버튼 활성화 조건:
        # 1. 직 이름이 입력되어 있는 경우
        # 2. 트리거 키가 설정되어 있는 경우
        # 3. 아이템 목록에 하나 이상의 아이템이 있는 경우
        # 4. 반복 횟수가 1이 아닌 경우
        has_logic_name = bool(self.LogicNameInput__QLineEdit.text().strip())
        has_trigger_key = bool(self.trigger_key_info)
        has_items = self.LogicItemList__QListWidget.count() > 0
        
        # 반복 횟수 확인
        try:
            repeat_count = self.RepeatCountInput__QSpinBox.value()
            has_different_repeat = repeat_count != 1
        except ValueError:
            has_different_repeat = False
        
        # 네 조건 중 하나라도 만족하면 버튼 활성화
        enable_button = has_logic_name or has_trigger_key or has_items or has_different_repeat
        
        self.NewLogicButton__QPushButton.setEnabled(enable_button)
        
    def _create_new_logic(self):
        """새 로직 버튼 클릭 시 호출되는 메서드"""
        self.clear_all()
        self.log_message.emit("새 로직을 만듭니다")
        
    def _edit_item(self):
        """선택된 아이템 수정"""
        current_item = self.LogicItemList__QListWidget.currentItem()
        if current_item:
            item_text = current_item.text()
            
            # 지연시간 아이템인 경우
            if item_text.startswith("지연시간"):
                try:
                    current_delay = float(item_text.split(":")[1].replace("초", "").strip())
                    
                    # QInputDialog 커스터마이징
                    dialog = QInputDialog(self)
                    dialog.setWindowTitle("지연시간 수정")
                    dialog.setLabelText("지연시간(초):")
                    dialog.setDoubleDecimals(3)  # 소수점 3자리까지 표시 (0.001초 단위)
                    dialog.setDoubleValue(current_delay)  # 현재 지연시간을 기본값으로 설정
                    dialog.setDoubleRange(0.001, 100.0)  # 0.001초 ~ 100초
                    dialog.setDoubleStep(0.001)  # 증가/감소 단위
                    
                    # 버튼 텍스트 변경
                    dialog.setOkButtonText("지연시간 저장")
                    dialog.setCancelButtonText("지연시간 입력 취소")
                    
                    if dialog.exec():
                        delay = dialog.doubleValue()
                        delay_text = f"지연시간 : {delay:.3f}초"
                        current_item.setText(delay_text)
                        # 순서 값과 content 유지
                        current_data = current_item.data(Qt.UserRole) or {}
                        current_data['content'] = delay_text  # content 필드 업데이트
                        current_item.setData(Qt.UserRole, current_data)
                        self.item_edited.emit(delay_text)
                        self.log_message.emit(f"지연시간이 {delay:.3f}초로 수정되었습니다")
                except ValueError:
                    self.log_message.emit("지연시간 형식이 올바르지 않습니다")
            # 키 입 아이템인 경우
            elif item_text.startswith("키 입력:"):
                key_parts = item_text.split(" --- ")
                if len(key_parts) == 2:
                    key_text = key_parts[0]
                    current_action = key_parts[1]  # 현재 액션 ("누르기" 또는 "떼기")
                    
                    # 액션 선택 대화상자
                    dialog = QMessageBox(self)
                    dialog.setWindowTitle("선택된 키의 키 입력 정보 수정")
                    dialog.setText("선택된 키의 입력 정보를 수정하세요")
                    dialog.setIcon(QMessageBox.Question)
                    
                    # 버튼 추가
                    press_button = dialog.addButton("누르기", QMessageBox.ActionRole)
                    release_button = dialog.addButton("떼기", QMessageBox.ActionRole)
                    cancel_button = dialog.addButton("취소", QMessageBox.RejectRole)
                    
                    # 현재 액션에 따라 기본 버튼 설정
                    if current_action == "누르기":
                        dialog.setDefaultButton(press_button)
                    else:
                        dialog.setDefaultButton(release_button)
                    
                    dialog.exec()
                    clicked_button = dialog.clickedButton()
                    
                    if clicked_button in [press_button, release_button]:
                        new_action = "누르기" if clicked_button == press_button else "떼기"
                        if new_action != current_action:
                            new_text = f"{key_text} --- {new_action}"
                            current_item.setText(new_text)
                            # 순서 값과 content 유지
                            current_data = current_item.data(Qt.UserRole) or {}
                            current_data['content'] = new_text  # content 필드 업데이트
                            current_item.setData(Qt.UserRole, current_data)
                            self.item_edited.emit(new_text)
                            self.log_message.emit(f"키 입력 액션이 '{new_action}'으로 변경되었습니다")
            else:
                self.item_edited.emit(item_text)

    def _delete_item(self):
        """선택된 아이템 삭제"""
        selected_items = self.LogicItemList__QListWidget.selectedItems()
        if selected_items:
            for item in selected_items:
                row = self.LogicItemList__QListWidget.row(item)
                item = self.LogicItemList__QListWidget.takeItem(row)
                self.item_deleted.emit(item.text())
            # 아이템 삭제 후 순서 재정렬
            for i in range(self.LogicItemList__QListWidget.count()):
                item = self.LogicItemList__QListWidget.item(i)
                item_data = item.data(Qt.UserRole) or {}
                item_data['order'] = i + 1
                item.setData(Qt.UserRole, item_data)
            self.log_message.emit(f"{len(selected_items)}개의 로직 구성 아이템이 삭제되습니다")

    def _on_nested_checkbox_changed(self, state):
        """중첩로직용 체크박스 상태 변경 시 호출"""
        is_nested = state == Qt.CheckState.Checked.value
        
        # 트리거 키 입력 UI 비활성화/활성화
        self.TriggerKeyInputWidget__KeyInputWidget.setEnabled(not is_nested)
        
        if is_nested:
            # 중첩로직용일 경우 트리거 키 보 초기화
            self.trigger_key_info = None
            self.TriggerKeyInfoLabel__QLabel.clear()
            # 트리거 키 입력 위젯 초기화
            self.TriggerKeyInputWidget__KeyInputWidget.clear_key()

    def get_logic_data(self):
        """기존 메서드 수정"""
        data = {
            'name': self.name_input.text(),
            'repeat_count': self.repeat_input.value(),
            'items': self.item_list.get_items(),
            'is_nested': self.is_nested_checkbox.isChecked()
        }
        
        # 중첩로직용이 아닐 경우에만 트리거 키 추가
        if not data['is_nested']:
            data['trigger_key'] = self.trigger_key
            
        return data

    def set_logic_data(self, logic_data):
        """기존 메서드 수정"""
        self.name_input.setText(logic_data.get('name', ''))
        self.repeat_input.setValue(logic_data.get('repeat_count', 1))
        self.item_list.set_items(logic_data.get('items', []))
        
        # 중첩로직 여부 설정
        is_nested = logic_data.get('is_nested', False)
        self.is_nested_checkbox.setChecked(is_nested)
        
        # 중첩로직이 아닐 경우에만 트리거 키 설정
        if not is_nested:
            self.trigger_key = logic_data.get('trigger_key')
            if self.trigger_key:
                self.trigger_key_button.setText(self.trigger_key.get('key_code', '트리거 키'))

    def clear_logic_info(self):
        """로직 정보 초기화"""
        try:
            # 로직 이름 초기화
            self.LogicNameInput__QLineEdit.clear()
            
            # 트리거 키 초기화
            self.TriggerKeyInput__QLineEdit.clear()
            self.trigger_key_info = {}
            
            # 반복 횟수 초기화
            self.RepeatCountInput__QSpinBox.setValue(1)
            
            # 중첩 로직용 체크박스 초기화
            self.IsNestedCheckBox__QCheckBox.setChecked(False)
            
            # 로직 아이템 목록 초기화
            self.LogicItemList__QListWidget.clear()
            
            # 로직 아이템 정보 초기화
            self.logic_items.clear()
            
            # 현재 편집 중인 로직 ID 초기화
            self.current_logic_id = None
            
            self.log_message.emit("로직 정보가 초기화되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"로직 정보 초기화 중 오류 발생: {str(e)}")
