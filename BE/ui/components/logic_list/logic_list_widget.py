from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import json
import os
import uuid

from ...constants.styles import (FRAME_STYLE, LIST_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import LOGIC_LIST_WIDTH, BASIC_SECTION_HEIGHT, LOGIC_BUTTON_WIDTH
from BE.settings.settings_manager import SettingsManager

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
        self.saved_logics = {}  # 저장된 로직들을 관리하는 딕셔너리: {uuid: 로직 정보}
        self.settings_manager = SettingsManager()
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
            self.save_logics_to_settings()
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
            self.save_logics_to_settings()
        except Exception as e:
            self.log_message.emit(f"아이템 이동 중 오류 발생: {e}")

    def on_logic_saved(self, logic_info):
        """로직이 저장되었을 때 호출되는 메서드"""
        try:
            # settings_manager를 통해 로직 저장
            ordered_logic = self.settings_manager.save_logic(logic_info)
            
            # 로직 목록에 추가
            self._add_logic_to_list(ordered_logic)
            
            self.log_message.emit(f"새 로직 '{logic_info.get('name', '')}'이(가) 저장되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"로직 저장 중 오류 발생: {str(e)}")

    def on_logic_updated(self, original_name, logic_info):
        """로직이 수정되었을 때 호출되는 메서드"""
        try:
            # 기존 로직 ID 찾기
            logic_id = None
            for id, logic in self.settings_manager.settings.get('logics', {}).items():
                if logic.get('name') == original_name:
                    logic_id = id
                    break
            
            if logic_id:
                # settings_manager를 통해 로직 업데이트
                ordered_logic = self.settings_manager.save_logic(logic_id, logic_info)
                
                # 목록 아이템 업데이트
                self._update_logic_in_list(ordered_logic)
                
                self.log_message.emit(f"로직 '{logic_info.get('name', '')}'이(가) 업데이트되었습니다.")
            else:
                self.log_message.emit(f"업데이트할 로직을 찾을 수 없습니다: {original_name}")
            
        except Exception as e:
            self.log_message.emit(f"로직 업데이트 중 오류 발생: {str(e)}")

    def load_saved_logics(self):
        """저장된 로직 정보 불러오기"""
        try:
            # settings_manager를 통해 로직 정보 불러오기
            self.saved_logics = self.settings_manager.load_logics()
            
            # 리스트 위젯에 로직 추가 (order 기준으로 정렬)
            self.SavedLogicList__QListWidget.clear()
            
            # logic_id와 함께 정렬
            logic_items = [(logic_id, logic) for logic_id, logic in self.saved_logics.items()]
            sorted_logic_items = sorted(logic_items, key=lambda x: x[1].get('order', float('inf')))
            
            for logic_id, logic in sorted_logic_items:
                display_text = self._format_logic_item_text(logic)
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, {'logic_id': logic_id})  # 로직 ID 저장
                self.SavedLogicList__QListWidget.addItem(item)
                
            self.log_message.emit(f"{len(sorted_logic_items)}개의 로직을 불러왔습니다.")
        except Exception as e:
            self.log_message.emit(f"로직 정보를 불러오는 중 오류 발생: {e}")

    def _format_logic_item_text(self, logic_info):
        """로직 아이템의 표시 텍스트를 생성하는 메서드"""
        if not logic_info:  # logic_info가 None인 경우 처리
            return ""
        name = logic_info.get('name', '')  # name이 없는 경우 빈 문자열 반환
        trigger_key = logic_info.get('trigger_key', {})
        if trigger_key and 'key_code' in trigger_key:
            key_text = trigger_key['key_code']
            modifiers = trigger_key.get('modifiers', 0)
            
            # 수정자 키 텍스트 생성
            modifier_text = []
            if modifiers & 1:  # Alt
                modifier_text.append("Alt")
            if modifiers & 2:  # Ctrl
                modifier_text.append("Ctrl")
            if modifiers & 4:  # Shift
                modifier_text.append("Shift")
            if modifiers & 8:  # Win
                modifier_text.append("Win")
                
            # 수정자 키가 있는 경우 조합하여 표시
            if modifier_text:
                return f"[ {name} ] --- {' + '.join(modifier_text)} + {key_text}"
            else:
                return f"[ {name} ] --- {key_text}"
        return f"[ {name} ]"

    def _get_logic_name_from_text(self, text):
        """표시 텍스트에서 로직 이름을 추출하는 메서드"""
        try:
            return text.split(' -- ')[0]
        except (AttributeError, IndexError):
            return text

    def save_logics_to_settings(self):
        """현재 로직 정보를 settings.json에 저장"""
        try:
            # 현재 리스트 위젯의 순서대로 order 값 업데이트 (1부터 시작)
            for i in range(self.SavedLogicList__QListWidget.count()):
                item = self.SavedLogicList__QListWidget.item(i)
                if not item:
                    continue
                    
                item_data = item.data(Qt.UserRole)
                if not item_data or 'logic_id' not in item_data:
                    continue
                    
                logic_id = item_data['logic_id']
                if logic_id in self.saved_logics:
                    self.saved_logics[logic_id]['order'] = i + 1  # order를 1부터 시작하도록 수정
            
            # settings_manager를 통해 로직 정보 저장
            self.settings_manager.save_logics(self.saved_logics)
        except Exception as e:
            self.log_message.emit(f"설정 저장 중 오류 발생: {e}")
        
    def _item_double_clicked(self, item):
        """로직 불러오기 방법 - 더블클릭으로 호출"""
        if not item:  # item이 None인 경우 처리
            return
        
        item_data = item.data(Qt.UserRole)
        if not item_data or 'logic_id' not in item_data:
            return
            
        logic_id = item_data['logic_id']
        if logic_id in self.saved_logics:
            logic_info = self.saved_logics[logic_id]
            name = logic_info['name']
            self.logic_selected.emit(name)  # 로직 선택 시그널 발생
            self.log_message.emit(f"로직 데이터: {logic_info}")
            self.edit_logic.emit(logic_info)
            
    def _edit_item(self):
        """선택된 로직 불러오기"""
        current_item = self.SavedLogicList__QListWidget.currentItem()
        if not current_item:
            return
            
        item_data = current_item.data(Qt.UserRole)
        if not item_data or 'logic_id' not in item_data:
            return
            
        logic_id = item_data['logic_id']
        if logic_id in self.saved_logics:
            logic_info = self.saved_logics[logic_id]
            self.log_message.emit(f"로직 데이터: {logic_info}")
            self.edit_logic.emit(logic_info)

    def _delete_item(self):
        """선택된 아이템 삭제"""
        current_item = self.SavedLogicList__QListWidget.currentItem()
        if not current_item:
            return
            
        item_data = current_item.data(Qt.UserRole)
        if not item_data or 'logic_id' not in item_data:
            return
            
        logic_id = item_data['logic_id']
        if logic_id in self.saved_logics:
            logic_info = self.saved_logics[logic_id]
            name = logic_info['name']
            
            reply = QMessageBox.question(
                self, 
                '로직 삭제', 
                f'로직 "{name}"을(를) 삭제하시겠습니까?',
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # 로직 삭제
                del self.saved_logics[logic_id]
                # 리스트에서 아이템 제거
                self.SavedLogicList__QListWidget.takeItem(self.SavedLogicList__QListWidget.row(current_item))
                self.save_logics_to_settings()
                self.item_deleted.emit(name)  # 아이템 삭제 시그널 발생
                self.log_message.emit(f'로직 "{name}"이(가) 삭제되었습니다')

    def _update_logic_in_list(self, logic_info):
        """리스트에서 로직 정보를 업데이트"""
        if not logic_info or not isinstance(logic_info, dict):
            return
            
        name = logic_info.get('name')
        if not name:
            return
            
        # 리스트에서 해당 로직 찾기
        for i in range(self.SavedLogicList__QListWidget.count()):
            item = self.SavedLogicList__QListWidget.item(i)
            if item and item.data(Qt.UserRole) == logic_info.get('id'):
                # 아이템 텍스트 업데이트
                item.setText(self._format_logic_item_text(logic_info))
                break

    def _add_logic_to_list(self, logic_info):
        """로직 목록에 아이템 추가"""
        if not logic_info or not isinstance(logic_info, dict):
            return
            
        name = logic_info.get('name')
        if not name:
            return
            
        # 로직 아이템 텍스트 생성
        display_text = self._format_logic_item_text(logic_info)
        
        # 아이템 생성
        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, {'logic_id': logic_info.get('id')})  # 로직 ID 저장
        
        # 아이템 추가
        self.SavedLogicList__QListWidget.addItem(item)
