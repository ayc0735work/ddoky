from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import json
import os

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
    edit_logic = Signal(dict)  # 로직 불러오기 시그널 (로직 정보)
    log_message = Signal(str)  # 로그 메시지 시그널
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.saved_logics = {}  # 저장된 로직들을 관리하는 딕셔너리: {이름: 로직 정보}
        self.load_saved_logics()  # 저장된 로직 정보 불러오기
        
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedSize(LOGIC_LIST_WIDTH, BASIC_SECTION_HEIGHT)
        
        # 메인 레이아웃
        LogicListLayout__QVBoxLayout = QVBoxLayout()
        LogicListLayout__QVBoxLayout.setAlignment(Qt.AlignmentFlag.AlignTop)
        LogicListLayout__QVBoxLayout.setContentsMargins(10, 10, 10, 10)
        LogicListLayout__QVBoxLayout.setSpacing(10)
        
        # 타이틀
        LogicListTitle__QLabel = QLabel("만든 로직 영역")
        LogicListTitle__QLabel.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        LogicListLayout__QVBoxLayout.addWidget(LogicListTitle__QLabel)
        
        # 리스트 위젯
        self.SavedLogicList__QListWidget = QListWidget()
        self.SavedLogicList__QListWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.SavedLogicList__QListWidget.setStyleSheet(LIST_STYLE)
        self.SavedLogicList__QListWidget.setSelectionMode(QListWidget.ExtendedSelection)  # 다중 선택 모드 활성화
        self.SavedLogicList__QListWidget.itemSelectionChanged.connect(self._on_selection_changed)
        self.SavedLogicList__QListWidget.itemDoubleClicked.connect(self._item_double_clicked)
        LogicListLayout__QVBoxLayout.addWidget(self.SavedLogicList__QListWidget)
        
        # 버튼 그룹 레이아웃
        LogicControlSection__QHBoxLayout = QHBoxLayout()
        LogicControlSection__QHBoxLayout.setContentsMargins(0, 0, 0, 0)
        LogicControlSection__QHBoxLayout.setSpacing(5)
        
        # 버튼 생성
        self.MoveUpButton__QPushButton = QPushButton("위로")
        self.MoveDownButton__QPushButton = QPushButton("아래로")
        self.LoadLogicButton__QPushButton = QPushButton("로직 불러오기")
        self.DeleteLogicButton__QPushButton = QPushButton("로직 삭제")
        
        # 버튼 설정
        self.MoveUpButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH - 30)
        self.MoveDownButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH - 30)
        self.LoadLogicButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH + 30)
        self.DeleteLogicButton__QPushButton.setFixedWidth(LOGIC_BUTTON_WIDTH)
        
        for btn in [self.MoveUpButton__QPushButton, self.MoveDownButton__QPushButton, 
                   self.LoadLogicButton__QPushButton, self.DeleteLogicButton__QPushButton]:
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setEnabled(False)
            LogicControlSection__QHBoxLayout.addWidget(btn)
        
        LogicListLayout__QVBoxLayout.addLayout(LogicControlSection__QHBoxLayout)
        self.setLayout(LogicListLayout__QVBoxLayout)
        
        # 버튼 시그널 연결
        self.MoveUpButton__QPushButton.clicked.connect(self._move_item_up)
        self.MoveDownButton__QPushButton.clicked.connect(self._move_item_down)
        self.LoadLogicButton__QPushButton.clicked.connect(self._edit_item)
        self.DeleteLogicButton__QPushButton.clicked.connect(self._delete_item)
        
    def _on_selection_changed(self):
        """리스트 아이템 선택이 변경되었을 때의 처리"""
        selected_items = self.SavedLogicList__QListWidget.selectedItems()
        has_selection = len(selected_items) > 0
        
        # 버튼 활성화/비활성화
        current_row = self.SavedLogicList__QListWidget.currentRow()
        self.MoveUpButton__QPushButton.setEnabled(has_selection and current_row > 0)
        self.MoveDownButton__QPushButton.setEnabled(has_selection and current_row < self.SavedLogicList__QListWidget.count() - 1)
        self.LoadLogicButton__QPushButton.setEnabled(len(selected_items) == 1)  # 수정은 단일 선택만 가능
        self.DeleteLogicButton__QPushButton.setEnabled(has_selection)  # 삭제는 다중 선택 가능
        
        # 선택된 아이템이 있고 단일 선택인 경우에만 시그널 발생
        if has_selection and len(selected_items) == 1:
            self.logic_selected.emit(selected_items[0].text())
            
    def _move_item_up(self):
        """현재 선택된 아이템을 위로 이동"""
        current_row = self.SavedLogicList__QListWidget.currentRow()
        if current_row > 0:
            current_item = self.SavedLogicList__QListWidget.takeItem(current_row)
            self.SavedLogicList__QListWidget.insertItem(current_row - 1, current_item)
            self.SavedLogicList__QListWidget.setCurrentItem(current_item)
            self.item_moved.emit()
            
    def _move_item_down(self):
        """현재 선택된 아이템을 아래로 이동"""
        current_row = self.SavedLogicList__QListWidget.currentRow()
        if current_row < self.SavedLogicList__QListWidget.count() - 1:
            current_item = self.SavedLogicList__QListWidget.takeItem(current_row)
            self.SavedLogicList__QListWidget.insertItem(current_row + 1, current_item)
            self.SavedLogicList__QListWidget.setCurrentItem(current_item)
            self.item_moved.emit()
            
    def on_logic_saved(self, logic_info):
        """로직이 저장되었을 때 호출되는 메서드"""
        name = logic_info['name']
        self.saved_logics[name] = logic_info
        
        # 리스트에 아이템 추가
        items = self.SavedLogicList__QListWidget.findItems(name, Qt.MatchExactly)
        if not items:
            item = QListWidgetItem(name)
            self.SavedLogicList__QListWidget.addItem(item)
        
        self.log_message.emit(f"로직 '{name}'이(가) 저장되었습니다")
        self.save_logics_to_settings()  # settings.json에 저장
        
    def on_logic_updated(self, original_name, logic_info):
        """로직이 수정되었을 때 호출되는 메서드"""
        name = logic_info['name']
        
        # 기존 이름의 로직 제거
        if original_name in self.saved_logics:
            del self.saved_logics[original_name]
        
        # 새 이름으로 로직 저장
        self.saved_logics[name] = logic_info
        
        # 리스트 아이템 텍스트 업데이트
        for i in range(self.SavedLogicList__QListWidget.count()):
            item = self.SavedLogicList__QListWidget.item(i)
            if item.text() == original_name:
                item.setText(name)
                break
                
        self.log_message.emit(f"로직 '{name}'이(가) 업데이트되었습니다")
        self.save_logics_to_settings()  # settings.json에 저장
        
    def load_saved_logics(self):
        """저장된 로직 정보를 settings.json에서 불러옴"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'settings.json')
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    if 'logics' in settings:
                        self.saved_logics = settings['logics']
                        # order 값을 기준으로 정렬하여 리스트에 추가
                        sorted_logics = sorted(self.saved_logics.items(), key=lambda x: x[1].get('order', float('inf')))
                        for logic_name, _ in sorted_logics:
                            item = QListWidgetItem(logic_name)
                            self.SavedLogicList__QListWidget.addItem(item)
        except Exception as e:
            self.log_message.emit(f"로직 정보를 불러오는 중 오류 발생: {str(e)}")

    def save_logics_to_settings(self):
        """현재 로직 정보를 settings.json에 저장"""
        try:
            settings_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'settings.json')
            settings = {}
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            
            # 저장을 위해 로직 정보 복사 및 수정
            logics_to_save = {}
            # 현재 리스트 위젯의 순서대로 로직 저장
            for i in range(self.SavedLogicList__QListWidget.count()):
                item = self.SavedLogicList__QListWidget.item(i)
                name = item.text()
                if name in self.saved_logics:
                    logic_info = self.saved_logics[name]
                    # 딕셔너리 깊은 복사
                    logic_copy = json.loads(json.dumps({
                        'name': logic_info['name'],
                        'items': logic_info['items'],
                        'repeat_count': logic_info.get('repeat_count', 1),  # 반복 횟수 추가
                        'order': i + 1  # 순서 정보 추가 (1부터 시작)
                    }))
                    
                    # trigger_key 정보 처리
                    if 'trigger_key' in logic_info:
                        trigger_key = logic_info['trigger_key']
                        modifiers = trigger_key.get('modifiers')
                        # KeyboardModifier 객체인 경우 value 속성을 사용하여 정수값 얻기
                        modifiers_value = modifiers.value if hasattr(modifiers, 'value') else (0 if modifiers is None else modifiers)
                        
                        logic_copy['trigger_key'] = {
                            'key_code': trigger_key.get('key_code', ''),
                            'scan_code': trigger_key.get('scan_code', 0),
                            'virtual_key': trigger_key.get('virtual_key', 0),
                            'display_text': trigger_key.get('display_text', ''),
                            'modifiers': modifiers_value
                        }
                    
                    logics_to_save[name] = logic_copy
            
            settings['logics'] = logics_to_save
            
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            
            self.log_message.emit("로직 정보가 저장되었습니다")
        except Exception as e:
            self.log_message.emit(f"로직 정보를 저장하는 중 오류 발생: {str(e)}")
        
    def _item_double_clicked(self, item):
        """로직 불러오기 방법 - 더블클릭으로 호출"""
        logic_name = item.text()
        if logic_name in self.saved_logics:
            logic_info = self.saved_logics[logic_name]
            self.log_message.emit(f"로직 데이터: {logic_info}")
            self.edit_logic.emit(logic_info)
            
    def _edit_item(self):
        """선택된 로직 불러오기"""
        current_item = self.SavedLogicList__QListWidget.currentItem()
        if current_item:
            logic_name = current_item.text()
            if logic_name in self.saved_logics:
                logic_info = self.saved_logics[logic_name]
                self.edit_logic.emit(logic_info)
            
    def _delete_item(self):
        """선택된 아이템 삭제"""
        current_item = self.SavedLogicList__QListWidget.currentItem()
        if current_item:
            logic_name = current_item.text()
            if logic_name in self.saved_logics:
                del self.saved_logics[logic_name]
                self.SavedLogicList__QListWidget.takeItem(self.SavedLogicList__QListWidget.row(current_item))
                self.log_message.emit(f"로직 '{logic_name}'이(가) 삭제되었습니다")
                self.item_deleted.emit(logic_name)
                self.save_logics_to_settings()  # settings.json에 저장
