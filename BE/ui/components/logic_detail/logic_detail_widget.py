from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QLineEdit, QInputDialog)
from PySide6.QtCore import Qt, Signal, QObject, QEvent
from PySide6.QtGui import QFont, QGuiApplication, QIntValidator

from ...constants.styles import (FRAME_STYLE, LIST_STYLE, BUTTON_STYLE, CONTAINER_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import (LOGIC_DETAIL_WIDTH, BASIC_SECTION_HEIGHT,
                                 LOGIC_BUTTON_WIDTH)
from ....utils.key_handler import (KeyboardHook, get_key_display_text, get_key_location,
                                get_modifier_text, format_key_info)
from ..common.key_input_widget import KeyInputWidget  

class LogicDetailWidget(QFrame):
    """로직 상세 내용을 표시하고 관리하는 위젯"""
    
    # 시그널 정의
    item_moved = Signal()  # 아이템이 이동되었을 때
    item_edited = Signal(str)  # 아이템이 수정되었을 때
    item_deleted = Signal(str)  # 아이템이 삭제되었을 때
    logic_name_saved = Signal(str)  # 로직 이름이 저장되었을 때
    log_message = Signal(str)  # 로그 메시지 시그널
    logic_saved = Signal(dict)  # 로직 저장 시그널 (로직 정보)
    logic_updated = Signal(str, dict)  # 로직 불러오기 시그널 (원래 이름, 로직 정보)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.edit_mode = False  # 수정 모드 여부
        self.last_key_info = None
        self.keyboard_hook = None
        self.trigger_key_info = None  # 트리거 키 정보
        self.original_name = None  # 원래 이름
        self.copied_items = []  # 복사된 아이템들 저장 (리스트로 변경)
        
        # 키보드 이벤트 필터 설치
        self.installEventFilter(self)
        
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
        name_label.setFixedWidth(70)
        name_layout.addWidget(name_label)
        
        # 로직 이름 입력
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("로직의 이름을 입력하세요")
        name_layout.addWidget(self.name_input)
        
        # 로직 저장 버튼
        self.save_btn = QPushButton("로직 저장")
        self.save_btn.setStyleSheet(BUTTON_STYLE)
        self.save_btn.clicked.connect(self._save_logic_name)
        name_layout.addWidget(self.save_btn)
        
        layout.addLayout(name_layout)
        
        # 트리거 키 정보 영역
        trigger_key_layout = QVBoxLayout()  # 수직 레이아웃으로 변경
        trigger_key_layout.setContentsMargins(0, 0, 0, 0)
        trigger_key_layout.setSpacing(5)
        
        # 트리거 키 입력 레이아웃
        key_input_layout = QHBoxLayout()
        key_input_layout.setContentsMargins(0, 0, 0, 0)
        key_input_layout.setSpacing(5)
        
        # 트리거 키 입력 라벨
        trigger_label = QLabel("트리거 키:")
        trigger_label.setFixedWidth(70)
        key_input_layout.addWidget(trigger_label)
        
        # 트리거 키 입력 위젯
        self.key_input = KeyInputWidget(self, show_details=False)
        self.key_input.key_input_changed.connect(self._on_key_input_changed)
        key_input_layout.addWidget(self.key_input)
        
        trigger_key_layout.addLayout(key_input_layout)
        
        # 트리거 키 정보 라벨
        self.key_info_label = QLabel()
        self.key_info_label.setStyleSheet(CONTAINER_STYLE)
        self.key_info_label.mousePressEvent = self._copy_key_info_to_clipboard
        trigger_key_layout.addWidget(self.key_info_label)
        
        layout.addLayout(trigger_key_layout)
        
        # 기능 선택 레이아웃
        function_layout = QHBoxLayout()
        function_layout.setContentsMargins(0, 0, 0, 0)
        function_layout.setSpacing(5)
        
        # 반복 횟수 입력 레이아웃
        repeat_layout = QHBoxLayout()
        repeat_layout.setContentsMargins(0, 0, 0, 0)
        repeat_layout.setSpacing(5)
        
        # 반복 횟수 입력 필드
        self.repeat_input = QLineEdit()
        self.repeat_input.setFixedWidth(70)
        self.repeat_input.setAlignment(Qt.AlignRight)
        # 숫자만 입력 가능하도록 설정
        self.repeat_input.setValidator(QIntValidator(1, 9999))
        self.repeat_input.setText("1")  # 기본값 설정
        repeat_layout.addWidget(self.repeat_input)
        
        # 반복 횟수 라벨
        repeat_label = QLabel("회 반복")
        repeat_layout.addWidget(repeat_label)
        
        repeat_layout.addStretch()  # 나머지 공간을 채움
        
        function_layout.addLayout(repeat_layout)
        function_layout.addStretch()  # 나머지 공간을 채움
        
        layout.addLayout(function_layout)
        
        # 리스트 위젯
        self.list_widget = QListWidget()
        self.list_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.list_widget.setStyleSheet(LIST_STYLE)
        self.list_widget.setSelectionMode(QListWidget.ExtendedSelection)  # 다중 선택 모드 활성화
        self.list_widget.itemSelectionChanged.connect(self._on_selection_changed)
        self.list_widget.itemDoubleClicked.connect(self._edit_item)  # 더블클릭 시그널 연결
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
        self.edit_btn = QPushButton("항목 수정")
        self.edit_btn.setFixedWidth(LOGIC_BUTTON_WIDTH)
        self.edit_btn.setStyleSheet(BUTTON_STYLE)
        self.edit_btn.setEnabled(False)
        button_group.addWidget(self.edit_btn)
        
        # 삭제 버튼
        self.delete_btn = QPushButton("항목 삭제")
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
        """리스트 아이템 선택이 변경되었을 때의 처리"""
        selected_items = self.list_widget.selectedItems()
        has_selection = len(selected_items) > 0
        
        # 버튼 활성화/비활성화
        current_row = self.list_widget.currentRow()
        self.up_btn.setEnabled(has_selection and current_row > 0)
        self.down_btn.setEnabled(has_selection and current_row < self.list_widget.count() - 1)
        self.edit_btn.setEnabled(len(selected_items) == 1)  # 수정은 단일 선택만 가능
        self.delete_btn.setEnabled(has_selection)  # 삭제는 다중 선택 가능

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
                        self.item_edited.emit(delay_text)
                        self.log_message.emit(f"지연시간이 {delay:.3f}초로 수정되었습니다")
                except ValueError:
                    self.log_message.emit("지연시간 형식이 올바르지 않습니다")
            else:
                self.item_edited.emit(item_text)
            
    def _delete_item(self):
        """선택된 아이템 삭제"""
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            for item in selected_items:
                row = self.list_widget.row(item)
                item = self.list_widget.takeItem(row)
                self.item_deleted.emit(item.text())
            self.log_message.emit(f"{len(selected_items)}개의 항목이 삭제되었습니다")

    def clear_all(self):
        """모든 입력과 상태를 초기화"""
        self.name_input.clear()           # 로직 이름 초기화
        self.list_widget.clear()          # 목록 초기화
        self.key_input.clear_key()        # 트리거 키 입력 초기화
        self.key_info_label.clear()       # 트리거 키 정보 초기화
        self.trigger_key_info = None      # 트리거 키 정보 초기화
        self.edit_mode = False            # 수정 모드 해제
        self.original_name = None         # 원래 이름 초기화

    def _on_key_input_changed(self, key_info):
        """키 입력이 변경되었을 때"""
        if not key_info:  # 키 정보가 비어있으면 라벨 초기화
            self.key_info_label.clear()
            return
            
        self.key_info_label.setText(format_key_info(key_info))
        self.trigger_key_info = key_info  # 트리거 키 정보 저장

    def _save_logic_name(self):
        """로직 이름을 저장"""
        name = self.name_input.text().strip()
        if not name:
            self.log_message.emit("로직 이름을 입력하세요")
            return
        
        # 아이템 목록이 비어있는지 확인
        if not self.has_items():
            self.log_message.emit("로직에 아이템을 추가하세요")
            return
        
        # 트리거 키가 설정되어 있는지 확인
        if not self.trigger_key_info:
            self.log_message.emit("트리거 키를 설정하세요")
            return
        
        # 아이템 목록 가져오기
        items = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item_text = item.text()
            
            # 키 입력 아이템인 경우
            if item_text.startswith("키 입력:"):
                key_parts = item_text.split(" --- ")
                if len(key_parts) == 2:
                    key_text = key_parts[0].replace("키 입력: ", "").strip()
                    action = key_parts[1]  # "누르기" 또는 "떼기"
                    
                    # 수정자 키가 있는 경우 처리
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
                        '방향키 아래쪽 ↓': win32con.VK_DOWN,
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
                    items.append({
                        "type": "key_input",
                        "key_code": key,
                        "scan_code": scan_code,
                        "virtual_key": virtual_key,
                        "modifiers": modifier_value,
                        "action": action,
                        "display_text": item_text
                    })
                else:
                    items.append({"type": "text", "content": item_text})
            # 지연시간 아이템인 경우
            elif item_text.startswith("지연시간"):
                items.append({
                    "type": "delay",
                    "duration": float(item_text.split(":")[1].replace("초", "").strip()),
                    "display_text": item_text
                })
            # 기타 아이템
            else:
                items.append({"type": "text", "content": item_text})
        
        # 로직 정보 생성
        logic_info = {
            "name": name,
            "items": items,
            "trigger_key": self.trigger_key_info,
            "repeat_count": int(self.repeat_input.text())  # 반복 횟수 추가
        }
        
        # 수정 모드인 경우 업데이트 시그널 발생
        if self.edit_mode and self.original_name:
            self.logic_updated.emit(self.original_name, logic_info)
            self.log_message.emit(f"로직 '{name}'이(가) 수정되었습니다")
        else:
            self.logic_saved.emit(logic_info)
            self.log_message.emit(f"로직 '{name}'이(가) 저장되었습니다")
        
        # 저장 후 초기화
        self.clear_all()

    def load_logic(self, logic_info):
        """로직 데이터 로드"""
        self.edit_mode = True
        self.name_input.setText(logic_info['name'])
        self.original_name = logic_info['name']  # 원래 이름 저장
        
        # 반복 횟수 설정
        repeat_count = logic_info.get('repeat_count', 1)  # 기본값 1
        self.repeat_input.setText(str(repeat_count))
        
        # 목록 아이템 로드
        self.list_widget.clear()
        for item in logic_info['items']:
            if isinstance(item, dict):
                if item['type'] == 'key_input':
                    self.add_item(item['display_text'])
                elif item['type'] == 'delay':
                    self.add_item(item['display_text'])
                else:
                    self.add_item(item['content'])
            else:
                self.add_item(item)  # 이전 형식 지원
        
        # 첫 번째 아이템 선택
        if self.list_widget.count() > 0:
            self.list_widget.setCurrentItem(self.list_widget.item(0))
            
        # 트리거 키 정보 로드
        if 'trigger_key' in logic_info:
            key_info = logic_info['trigger_key']
            self.trigger_key_info = key_info  # 트리거 키 정보 저장
            self.key_input.set_key_info(key_info)  # key_input 위젯에 키 정보 설정
            self.key_info_label.setText(format_key_info(key_info))  # 키 정보 표시

    def has_items(self):
        """목록에 아이템이 있는지 확인"""
        return self.list_widget.count() > 0

    def add_item(self, item_text):
        """아이템 추가
        
        Args:
            item_text (str): 추가할 아이템의 텍스트
        """
        item = QListWidgetItem(item_text)
        self.list_widget.addItem(item)

    def _copy_key_info_to_clipboard(self, event):
        """트리거 키 정보를 클립보드에 복사"""
        if self.key_info_label.text():
            clipboard = QGuiApplication.clipboard()
            clipboard.setText(self.key_info_label.text())
            self.log_message.emit("트리거 키 정보가 클립보드에 복사되었습니다")

    def _copy_item(self):
        """선택된 아이템들을 복사"""
        selected_items = self.list_widget.selectedItems()
        if selected_items:
            self.copied_items = [item.text() for item in selected_items]
            items_count = len(self.copied_items)
            self.log_message.emit(f"{items_count}개의 아이템이 복사되었습니다")
            
    def _paste_item(self):
        """복사된 아이템들을 현재 선택된 아이템 아래에 붙여넣기"""
        if not self.copied_items:
            self.log_message.emit("복사된 아이템이 없습니다")
            return
            
        current_row = self.list_widget.currentRow()
        if current_row == -1:  # 선택된 아이템이 없으면 마지막에 추가
            current_row = self.list_widget.count() - 1
        
        # 복사된 아이템들을 순서대로 추가
        first_inserted_item = None
        for i, item_text in enumerate(self.copied_items):
            new_item = QListWidgetItem(item_text)
            insert_row = current_row + 1 + i
            self.list_widget.insertItem(insert_row, new_item)
            if i == 0:
                first_inserted_item = new_item
    
        # 기존 선택 해제 후 첫 번째로 삽입된 아이템만 선택
        if first_inserted_item:
            self.list_widget.clearSelection()
            self.list_widget.setCurrentItem(first_inserted_item)
    
        items_count = len(self.copied_items)
        self.log_message.emit(f"{items_count}개의 아이템이 붙여넣기 되었습니다")

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
