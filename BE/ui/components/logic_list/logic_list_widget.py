from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont
import json
import os
import uuid
from datetime import datetime

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
        
        # 이벤트 필터 설치
        self.SavedLogicList__QListWidget.installEventFilter(self)
        self.copied_logic = None  # 복사된 로직 정보 저장용
        
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
            # 새 UUID 생성
            logic_id = str(uuid.uuid4())
            
            # order 값을 현재 리스트의 마지막 순서 + 1로 설정
            current_count = self.SavedLogicList__QListWidget.count()
            
            # 원본 로직의 아이템 정보가 있다면 복사
            original_logic_name = logic_info.get('name')
            if original_logic_name:
                for saved_logic_id, saved_logic in self.saved_logics.items():
                    if saved_logic.get('name') == original_logic_name:
                        # 기존 로직의 아이템 정보를 복사
                        logic_info['items'] = saved_logic.get('items', [])
                        break
            
            logic_info['order'] = current_count + 1
            
            # settings_manager를 통해 로직 저장
            updated_logic = self.settings_manager.save_logic(logic_id, logic_info)
            
            # 로직 목록에 추가
            self._add_logic_to_list(updated_logic, logic_id)
            
            self.log_message.emit(f"새 로직 '{logic_info.get('name', '')}'이(가) 저장되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"로직 저장 중 오류 발생: {str(e)}")

    def on_logic_updated(self, original_name, logic_info):
        """로직이 수정되었을 때 호출되는 메서드"""
        try:
            # 기존 로직 ID 찾기
            logics = self.settings_manager.load_logics()
            logic_id = None
            for id, logic in logics.items():
                if logic.get('name') == original_name:
                    logic_id = id
                    break
            
            if logic_id:
                # settings_manager를 통해 로직 업데이트
                updated_logic = self.settings_manager.save_logic(logic_id, logic_info)
                
                # 목록 아이템 업데이트
                self._update_logic_in_list(updated_logic)
                
                # 저장된 로직 목록 다시 로드
                self.load_saved_logics()
                
                self.log_message.emit(f"로직 '{logic_info.get('name', '')}'이(가) 업데이트되었습니다.")
            else:
                self.log_message.emit(f"업데이트할 로직을 찾을 수 없습니다: {original_name}")
            
        except Exception as e:
            self.log_message.emit(f"로직 업데이트 중 오류 발생: {str(e)}")

    def load_saved_logics(self):
        """저장된 로직 정보 불러오기"""
        try:
            # 기존 목록 초기화
            self.SavedLogicList__QListWidget.clear()
            self.saved_logics.clear()  # saved_logics 딕셔너리도 초기화
            
            # 설정 다시 로드
            self.settings_manager.reload_settings()
            
            # 로직 정보 가져오기
            logics = self.settings_manager.settings.get('logics', {})
            
            # order 값으로 정렬
            sorted_logics = sorted(logics.items(), key=lambda x: x[1].get('order', 0))
            
            # 순서대로 리스트에 추가만 하고 order는 변경하지 않음
            for logic_id, logic_info in sorted_logics:
                self._add_logic_to_list(logic_info, logic_id)
                
            self.log_message.emit("로직 목록을 불러왔습니다.")
            
        except Exception as e:
            self.log_message.emit(f"로직 목록 불러오기 중 오류 발생: {str(e)}")
            # 오류 발생 시 초기화
            self.SavedLogicList__QListWidget.clear()
            self.saved_logics.clear()
            
    def save_logics_to_settings(self):
        """현재 로직 목록을 설정에 저장"""
        try:
            # 현재 설정을 다시 로드하여 최신 상태 유지
            self.settings_manager.reload_settings()
            
            # 로직 목록을 순회하면서 order 값 업데이트
            updated_logics = {}
            for i in range(self.SavedLogicList__QListWidget.count()):
                item = self.SavedLogicList__QListWidget.item(i)
                if item:
                    logic_id = item.data(Qt.UserRole)
                    if logic_id in self.settings_manager.settings.get('logics', {}):
                        logic_info = self.settings_manager.settings['logics'][logic_id]
                        
                        # 첫 번째 아이템의 order는 1로 설정하고, 나머지는 2부터 순차적으로 증가
                        logic_info['order'] = 1 if i == 0 else i + 1
                        logic_info['updated_at'] = datetime.now().isoformat()
                        
                        # settings_manager를 통해 로직 저장 (필드 순서 정리)
                        updated_logic = self.settings_manager.save_logic(logic_id, logic_info)
                        updated_logics[logic_id] = updated_logic
            
            # 모든 로직이 성공적으로 저장되면 saved_logics 업데이트
            self.saved_logics = updated_logics
            
            # settings_manager의 settings도 업데이트
            self.settings_manager.settings['logics'] = updated_logics
            self.settings_manager._save_settings()
            
            self.log_message.emit("로직이 성공적으로 저장되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"로직 저장 중 오류 발생: {str(e)}")
            # 오류 발생 시 저장된 로직 다시 불러오기
            self.load_saved_logics()
            
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
            # �� 안의 내을 추출
            start = text.find('[') + 1
            end = text.find(']')
            if start > 0 and end > start:
                return text[start:end].strip()
            return text
        except (AttributeError, IndexError):
            return text

    def _item_double_clicked(self, item):
        """로직 불러오기 방법 - 더블클릭으로 호출"""
        if not item:
            return
        
        logic_id = item.data(Qt.UserRole)
        if not logic_id:
            return
        
        if logic_id in self.saved_logics:
            logic_info = self.saved_logics[logic_id]
            logic_info['id'] = logic_id  # UUID를 logic_info에 포함
            self.logic_selected.emit(logic_info['name'])
            self.log_message.emit(f"로직 데이터: {logic_info}")
            self.edit_logic.emit(logic_info)

    def _edit_item(self):
        """선택된 로직 불러오기"""
        current_item = self.SavedLogicList__QListWidget.currentItem()
        if not current_item:
            return
        
        logic_id = current_item.data(Qt.UserRole)
        if not logic_id:
            return
        
        if logic_id in self.saved_logics:
            logic_info = self.saved_logics[logic_id]
            logic_info['id'] = logic_id  # UUID를 logic_info에 포함
            self.log_message.emit(f"로직 데이터: {logic_info}")
            self.edit_logic.emit(logic_info)

    def _delete_item(self):
        """선택된 아이템 삭제"""
        selected_items = self.SavedLogicList__QListWidget.selectedItems()
        if not selected_items:
            return
        
        # 삭제 확인 메시지 표시
        if len(selected_items) == 1:
            logic_name = self._get_logic_name_from_text(selected_items[0].text())
            message = f'로직 "{logic_name}"을(를) 삭제하시겠습니까?'
        else:
            message = f'선택된 {len(selected_items)}개의 로직을 삭제하시겠습니까?'
        
        reply = QMessageBox.question(
            self, 
            '로직 삭제', 
            message,
            QMessageBox.Yes | QMessageBox.No, 
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # 선택된 모든 아이템 삭제
                for item in selected_items:
                    logic_id = item.data(Qt.UserRole)
                    if logic_id in self.saved_logics:
                        # saved_logics에서 삭제
                        del self.saved_logics[logic_id]
                        # settings에서도 삭제
                        if logic_id in self.settings_manager.settings.get('logics', {}):
                            del self.settings_manager.settings['logics'][logic_id]
                        # 리스트에서 아이템 제거
                        self.SavedLogicList__QListWidget.takeItem(
                            self.SavedLogicList__QListWidget.row(item)
                        )
                        # 삭제 시그널 발생
                        logic_name = self._get_logic_name_from_text(item.text())
                        self.item_deleted.emit(logic_name)
                
                # 변경사항 저장
                self.save_logics_to_settings()
                
                # 로그 메시지
                if len(selected_items) == 1:
                    self.log_message.emit(f'로직 "{logic_name}"이(가) 삭제되었습니다')
                else:
                    self.log_message.emit(f'{len(selected_items)}개의 로직이 삭제되었습니다')
                
            except Exception as e:
                self.log_message.emit(f"로직 삭제 중 오류 발생: {str(e)}")

    def _update_logic_in_list(self, logic_info):
        """리스트에서 로직 정보를 업데이트"""
        if not logic_info or not isinstance(logic_info, dict):
            return
            
        name = logic_info.get('name')
        if not name:
            return
            
        # 스트에서 해당 로직 찾기
        for i in range(self.SavedLogicList__QListWidget.count()):
            item = self.SavedLogicList__QListWidget.item(i)
            if item:
                logic_id = item.data(Qt.UserRole)
                if logic_id in self.saved_logics and self.saved_logics[logic_id]['name'] == name:
                    # 로직 정보 업데이트
                    self.saved_logics[logic_id] = logic_info
                    # 아이템 텍스트 업데이트
                    item.setText(self._format_logic_item_text(logic_info))
                    break

    def _add_logic_to_list(self, logic_info, logic_id):
        """로직 목록에 아이템 추가"""
        if not logic_info or not isinstance(logic_info, dict):
            return
            
        name = logic_info.get('name')
        if not name:
            return
            
        # 로직 아이템 텍스트 생성
        display_text = self._format_logic_item_text(logic_info)
        
        # QListWidgetItem 생성
        item = QListWidgetItem(display_text)
        item.setData(Qt.UserRole, logic_id)  # 로직 ID를 아이템 데이터로 저장
        
        # 리스트에 아이템 추가
        self.SavedLogicList__QListWidget.addItem(item)
        
        # 저장된 로직 딕셔너리��� 추가
        self.saved_logics[logic_id] = logic_info

    def _update_logic_item_text(self, item, logic_data):
        """로직 아이템 텍스트 업데이트"""
        name = logic_data.get('name', '무제')
        
        # 중첩로직용일 경우와 아닐 경우 표시 형식 구분
        if logic_data.get('is_nested', False):
            display_text = f"[ {name} ] --- 중첩로직용"
        else:
            trigger_key = logic_data.get('trigger_key', {})
            key_code = trigger_key.get('key_code', '미설정')
            display_text = f"[ {name} ] --- {key_code}"
            
        item.setText(display_text)

    def eventFilter(self, obj, event):
        """이벤트 필터"""
        if obj == self.SavedLogicList__QListWidget and event.type() == QEvent.KeyPress:
            modifiers = event.modifiers()
            key = event.key()
            
            # Ctrl+C: 복사
            if modifiers == Qt.ControlModifier and key == Qt.Key_C:
                self._copy_logic()
                return True
                
            # Ctrl+V: 붙여넣기
            elif modifiers == Qt.ControlModifier and key == Qt.Key_V:
                self._paste_logic()
                return True
                
            # Delete: 삭제
            elif key == Qt.Key_Delete:
                self._delete_item()  # 기존의 삭제 버튼과 동일한 메서드 호출
                return True
                
        return super().eventFilter(obj, event)

    def _copy_logic(self):
        """선택된 로직 복사"""
        current_item = self.SavedLogicList__QListWidget.currentItem()
        if not current_item:
            return

        try:
            # 원본 로직 정보 가져오기
            logic_id = current_item.data(Qt.UserRole)
            if not logic_id or logic_id not in self.saved_logics:
                return

            # 로직 정보 복사
            self.copied_logic = self.saved_logics[logic_id].copy()
            self.log_message.emit(f"로직 '{self.copied_logic['name']}'이(가) 복사되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"로직 복사 중 오류 발생: {str(e)}")

    def _paste_logic(self):
        """복사된 로직 붙여넣기"""
        if not self.copied_logic:
            self.log_message.emit("복사된 로직이 없습니다.")
            return

        try:
            # 현재 선택된 아이템의 위치 확인
            current_item = self.SavedLogicList__QListWidget.currentItem()
            if current_item:
                insert_position = self.SavedLogicList__QListWidget.row(current_item) + 1
            else:
                insert_position = self.SavedLogicList__QListWidget.count()

            # 새 로직 정보 생성
            new_logic = self.copied_logic.copy()
            new_logic_id = str(uuid.uuid4())
            
            # 이름 뒤에 "- 복제" 추가
            original_name = new_logic['name']
            new_logic['name'] = f"{original_name} - 복제"
            
            # 생성/수정 시간 업데이트
            current_time = datetime.now().isoformat()
            new_logic['created_at'] = current_time
            new_logic['updated_at'] = current_time
            
            # 선택된 아이템 이후의 모든 아이템의 order 값을 1씩 증가
            for i in range(insert_position, self.SavedLogicList__QListWidget.count()):
                item = self.SavedLogicList__QListWidget.item(i)
                if item:
                    logic_id = item.data(Qt.UserRole)
                    if logic_id in self.saved_logics:
                        self.saved_logics[logic_id]['order'] = i + 2

            # 새 로직의 order 값 설정
            new_logic['order'] = insert_position + 1
            
            # 새 로직 저장
            self.settings_manager.save_logic(new_logic_id, new_logic)
            
            # 리스트의 특정 위치에 추가
            self._add_logic_to_list(new_logic, new_logic_id)
            
            # 새로 추가된 아이템을 올바른 위치로 이동
            last_item = self.SavedLogicList__QListWidget.item(self.SavedLogicList__QListWidget.count() - 1)
            if last_item:
                self.SavedLogicList__QListWidget.takeItem(self.SavedLogicList__QListWidget.count() - 1)
                self.SavedLogicList__QListWidget.insertItem(insert_position, last_item)
                self.SavedLogicList__QListWidget.setCurrentItem(last_item)
            
            # 변경사항 저장
            self.save_logics_to_settings()
            
            self.log_message.emit(f"로직 '{original_name}'이(가) 붙여넣기되었습니다.")
            
        except Exception as e:
            self.log_message.emit(f"로직 붙여넣기 중 오류 발생: {str(e)}")
