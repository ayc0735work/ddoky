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
            logic_name = self._get_logic_name_from_text(selected_items[0].text())
            self.logic_selected.emit(logic_name)
            
    def _check_editing_logic(self, current_item):
        """현재 수정 중인 로직인지 확인
        
        Args:
            current_item: 현재 선택된 아이템
            
        Returns:
            bool: 항상 True 반환
        """
        return True
            
    def _move_item_up(self):
        """선택된 아이템을 위로 이동"""
        current_row = self.SavedLogicList__QListWidget.currentRow()
        if current_row <= 0:
            return

        # 현재 로직이 편집 중인지 확인
        current_item = self.SavedLogicList__QListWidget.currentItem()
        if not current_item:  # 아이템이 None인 경우
            return

        if not self._check_editing_logic(current_item):
            return

        try:
            # 아이템 이동
            item = self.SavedLogicList__QListWidget.takeItem(current_row)
            if not item:  # takeItem이 실패한 경우
                return
            self.SavedLogicList__QListWidget.insertItem(current_row - 1, item)
            self.SavedLogicList__QListWidget.setCurrentRow(current_row - 1)
            
            # 아이템 이동 시그널 발생
            self.item_moved.emit()
            
            # 변경사항 즉시 저장
            self.save_logics_to_settings()  # 순서 변경 즉시 저장
        except Exception as e:
            self.log_message.emit(f"아이템 이동 중 오류 발생: {e}")
            
    def _move_item_down(self):
        """선택된 아이템을 아래로 이동"""
        current_row = self.SavedLogicList__QListWidget.currentRow()
        if current_row < 0 or current_row >= self.SavedLogicList__QListWidget.count() - 1:
            return

        # 현재 로직이 편집 중인지 확인
        current_item = self.SavedLogicList__QListWidget.currentItem()
        if not current_item:  # 아이템이 None인 경우
            return

        if not self._check_editing_logic(current_item):
            return

        try:
            # 아이템 이동
            item = self.SavedLogicList__QListWidget.takeItem(current_row)
            if not item:  # takeItem이 실패한 경우
                return
            self.SavedLogicList__QListWidget.insertItem(current_row + 1, item)
            self.SavedLogicList__QListWidget.setCurrentRow(current_row + 1)
            
            # 아이템 이동 시그널 발생
            self.item_moved.emit()
            
            # 변경사항 즉시 저장
            self.save_logics_to_settings()  # 순서 변경 즉시 저장
        except Exception as e:
            self.log_message.emit(f"아이템 이동 중 오류 발생: {e}")

    def on_logic_saved(self, logic_info):
        """로직이 저장되었을 때 호출되는 메서드"""
        name = logic_info['name']
        self.saved_logics[name] = logic_info
        
        # 리스트에 아이템 추가
        items = self.SavedLogicList__QListWidget.findItems(name, Qt.MatchExactly)
        display_text = self._format_logic_item_text(logic_info)
        
        if items:
            items[0].setText(display_text)
        else:
            item = QListWidgetItem(display_text)
            self.SavedLogicList__QListWidget.addItem(item)
        
        self.log_message.emit(f"로직 '{name}'이(가) 저장되었습니다")
        self.save_logics_to_settings()  # settings.json에 저장

    def on_logic_updated(self, original_name, logic_info):
        """로직이 수정되었을 때 호출되는 메서드"""
        try:
            if not logic_info:  # logic_info가 None인 경우
                self.log_message.emit("업데이트할 로직 정보가 없습니다")
                return
                
            name = logic_info.get('name', '')  # 새 이름
            if not name:  # 새 이름이 비어있는 경우
                self.log_message.emit("업데이트할 로직의 이름이 없습니다")
                return
                
            # 새 이름이 이미 존재하고, 원래 이름과 다른 경우
            if name != original_name and name in self.saved_logics:
                self.log_message.emit(f"이미 '{name}' 이름의 로직이 존재합니다")
                return
            
            # 기존 이름의 로직 제거
            if original_name in self.saved_logics:
                del self.saved_logics[original_name]
            else:
                self.log_message.emit(f"원본 로직 '{original_name}'을(를) 찾을 수 없습니다")
                return
            
            # 새 이름으로 로직 저장
            self.saved_logics[name] = logic_info
            
            # 리스트 아이템 텍스트 업데이트
            display_text = self._format_logic_item_text(logic_info)
            item_found = False
            
            for i in range(self.SavedLogicList__QListWidget.count()):
                item = self.SavedLogicList__QListWidget.item(i)
                if not item:  # item이 None인 경우
                    continue
                    
                if self._get_logic_name_from_text(item.text()) == original_name:
                    item.setText(display_text)
                    item_found = True
                    break
            
            if not item_found:
                self.log_message.emit(f"리스트에서 로직 '{original_name}'을(를) 찾을 수 없습니다")
                return
                
            self.log_message.emit(f"로직 '{name}'이(가) 업데이트되었습니다")
            self.save_logics_to_settings()  # settings.json에 저장
            
            # 아이템이 수정되었음을 알림
            self.item_edited.emit(logic_info)
            
        except Exception as e:
            self.log_message.emit(f"로직 업데이트 중 오류 발생: {e}")

    def load_saved_logics(self):
        """저장된 로직 정보 불러오기"""
        try:
            # settings.json 파일 경로
            settings_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'settings.json')
            
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.saved_logics = settings.get('logics', {})
                    
                    # 리스트 위젯에 로직 추가 (order 기준으로 정렬)
                    self.SavedLogicList__QListWidget.clear()
                    sorted_logics = sorted(self.saved_logics.items(), key=lambda x: x[1].get('order', float('inf')))
                    for name, logic_info in sorted_logics:
                        display_text = self._format_logic_item_text(logic_info)
                        item = QListWidgetItem(display_text)
                        self.SavedLogicList__QListWidget.addItem(item)
            else:
                self.log_message.emit("설정 파일이 존재하지 않습니다")
        except Exception as e:
            self.log_message.emit(f"로직 정보를 불러오는 중 오류 발생: {e}")

    def _format_logic_item_text(self, logic_info):
        """로직 아이템의 표시 텍스트를 생성하는 메서드"""
        if not logic_info:  # logic_info가 None인 경우 처리
            return ""
        name = logic_info.get('name', '')  # name이 없는 경우 빈 문자열 반환
        trigger_key = logic_info.get('trigger_key', {})
        if trigger_key:
            try:
                key_code = trigger_key.get('key_code', '')
                if key_code:
                    return f"[ {name} ] --- {key_code}"
            except Exception as e:
                self.log_message.emit(f"트리거 키 정보 포맷 중 오류 발생: {e}")
                return name
        return name

    def _get_logic_name_from_text(self, text):
        """표시 텍스트에서 로직 이름을 추출하는 메서드"""
        try:
            return text.split(' -- ')[0]
        except (AttributeError, IndexError):
            return text

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
                if not item:  # item이 None인 경우 처리
                    continue
                name = self._get_logic_name_from_text(item.text())
                if name in self.saved_logics:
                    logic_info = self.saved_logics[name]
                    # 딕셔너리 깊은 복사
                    logic_copy = json.loads(json.dumps({
                        'name': logic_info['name'],
                        'items': logic_info.get('items', []),  # items가 없는 경우 빈 리스트 반환
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
        if not item:  # item이 None인 경우 처리
            return
        logic_name = self._get_logic_name_from_text(item.text())
        if logic_name in self.saved_logics:
            logic_info = self.saved_logics[logic_name]
            self.log_message.emit(f"로직 데이터: {logic_info}")
            self.edit_logic.emit(logic_info)
            
    def _edit_item(self):
        """선택된 로직 불러오기"""
        current_item = self.SavedLogicList__QListWidget.currentItem()
        if current_item:
            logic_name = self._get_logic_name_from_text(current_item.text())
            if logic_name in self.saved_logics:
                logic_info = self.saved_logics[logic_name]
                self.edit_logic.emit(logic_info)
            
    def _delete_item(self):
        """선택된 아이템 삭제"""
        current_item = self.SavedLogicList__QListWidget.currentItem()
        if current_item:
            logic_name = self._get_logic_name_from_text(current_item.text())
            if logic_name in self.saved_logics:
                del self.saved_logics[logic_name]
                self.SavedLogicList__QListWidget.takeItem(self.SavedLogicList__QListWidget.row(current_item))
                self.log_message.emit(f"로직 '{logic_name}'이(가) 삭제되었습니다")
                self.item_deleted.emit(logic_name)
                self.save_logics_to_settings()  # settings.json에 저장
