from PySide6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSizePolicy, QMessageBox)
from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtGui import QFont
import json
import os
import uuid
from datetime import datetime
import copy

from ...constants.styles import (FRAME_STYLE, LIST_STYLE, BUTTON_STYLE,
                             TITLE_FONT_FAMILY, SECTION_FONT_SIZE)
from ...constants.dimensions import LOGIC_LIST_WIDTH, BASIC_SECTION_HEIGHT, LOGIC_BUTTON_WIDTH
from BE.settings.settings_data_manager import SettingsManager

class LogicListWidget(QFrame):
    """로직 목록을 표시하고 관리하는 위젯"""
    
    # 시그널 정의
    logic_move_requested = Signal(str, int)  # logic_id, new_position
    logic_edit_requested = Signal(str, dict)  # logic_id, new_data
    logic_delete_requested = Signal(str)  # logic_id
    logic_copy_requested = Signal(str)  # logic_id
    logic_paste_requested = Signal()
    log_message = Signal(str)  # 로그 메시지
    logic_selected = Signal(str)  # 로직이 선택되었을 때 (로직 이름)
    edit_logic = Signal(dict)  # 로직 불러오기 시그널 (로직 정보)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
        # 이벤트 필터 설치
        self.logic_list.installEventFilter(self)
        
    def init_ui(self):
        """UI 초기화"""
        self.setStyleSheet(FRAME_STYLE)
        self.setFixedSize(LOGIC_LIST_WIDTH, BASIC_SECTION_HEIGHT)
        
        # 메인 레이아웃
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 타이틀
        title = QLabel("만든 로직 리스트")
        title.setFont(QFont(TITLE_FONT_FAMILY, SECTION_FONT_SIZE, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # 리스트 위젯
        self.logic_list = QListWidget()
        self.logic_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.logic_list.setStyleSheet(LIST_STYLE)
        self.logic_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.logic_list.itemSelectionChanged.connect(self._on_selection_changed)
        self.logic_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.logic_list)
        
        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)
        
        # 버튼 생성
        self.move_up_btn = QPushButton("위로")
        self.move_down_btn = QPushButton("아래로")
        self.edit_btn = QPushButton("로직 불러오기")
        self.delete_btn = QPushButton("로직 삭제")
        
        # 버튼 설정
        self.move_up_btn.setFixedWidth(LOGIC_BUTTON_WIDTH - 30)
        self.move_down_btn.setFixedWidth(LOGIC_BUTTON_WIDTH - 30)
        self.edit_btn.setFixedWidth(LOGIC_BUTTON_WIDTH + 30)
        self.delete_btn.setFixedWidth(LOGIC_BUTTON_WIDTH)
        
        for btn in [self.move_up_btn, self.move_down_btn, self.edit_btn, self.delete_btn]:
            btn.setStyleSheet(BUTTON_STYLE)
            btn.setEnabled(False)
            button_layout.addWidget(btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # 버튼 시그널 연결
        self.move_up_btn.clicked.connect(self._on_move_up_clicked)
        self.move_down_btn.clicked.connect(self._on_move_down_clicked)
        self.edit_btn.clicked.connect(self._on_edit_clicked)
        self.delete_btn.clicked.connect(self._on_delete_clicked)
        
    def _on_selection_changed(self):
        """리스트 아이템 선택이 변경되었을 때의 처리"""
        selected_items = self.logic_list.selectedItems()
        has_selection = len(selected_items) > 0
        
        # 버튼 활성화/비활성화
        current_row = self.logic_list.currentRow()
        self.move_up_btn.setEnabled(has_selection and current_row > 0)
        self.move_down_btn.setEnabled(has_selection and current_row < self.logic_list.count() - 1)
        self.edit_btn.setEnabled(len(selected_items) == 1)
        self.delete_btn.setEnabled(has_selection)
        
    def _on_move_up_clicked(self):
        """위로 버튼 클릭 처리"""
        current_item = self.logic_list.currentItem()
        if not current_item:
            return
            
        current_row = self.logic_list.currentRow()
        logic_id = current_item.data(Qt.UserRole)
        self.logic_move_requested.emit(logic_id, current_row - 1)
        
    def _on_move_down_clicked(self):
        """아래로 버튼 클릭 처리"""
        current_item = self.logic_list.currentItem()
        if not current_item:
            return
            
        current_row = self.logic_list.currentRow()
        logic_id = current_item.data(Qt.UserRole)
        self.logic_move_requested.emit(logic_id, current_row + 1)
        
    def _on_edit_clicked(self):
        """로직 불러오기 버튼 클릭 처리"""
        current_item = self.logic_list.currentItem()
        if not current_item:
            return
            
        # 설정 매니저를 통해 로직 정보 가져오기
        settings_manager = SettingsManager()
        logics = settings_manager.load_logics()
        logic_id = current_item.data(Qt.UserRole)
        
        if logic_id in logics:
            self.edit_logic.emit(logics[logic_id])
        
    def _on_item_double_clicked(self, item):
        """아이템 더블클릭 처리"""
        if not item:
            return
            
        # 설정 매니저를 통해 로직 정보 가져오기
        settings_manager = SettingsManager()
        logics = settings_manager.load_logics()
        logic_id = item.data(Qt.UserRole)
        
        if logic_id in logics:
            self.edit_logic.emit(logics[logic_id])
        
    def _on_delete_clicked(self):
        """삭제 버튼 클릭 처리"""
        selected_items = self.logic_list.selectedItems()
        if not selected_items:
            return
            
        # 삭제 확인 메시지
        if len(selected_items) == 1:
            message = f'로직 "{selected_items[0].text()}"을(를) 삭제하시겠습니까?'
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
            for item in selected_items:
                logic_id = item.data(Qt.UserRole)
                self.logic_delete_requested.emit(logic_id)
                
    def eventFilter(self, obj, event):
        """이벤트 필터"""
        if obj == self.logic_list and event.type() == QEvent.KeyPress:
            modifiers = event.modifiers()
            key = event.key()
            
            # Ctrl+C: 복사
            if modifiers == Qt.ControlModifier and key == Qt.Key_C:
                current_item = self.logic_list.currentItem()
                if current_item:
                    logic_id = current_item.data(Qt.UserRole)
                    self.logic_copy_requested.emit(logic_id)
                return True
                
            # Ctrl+V: 붙여넣기
            elif modifiers == Qt.ControlModifier and key == Qt.Key_V:
                self.logic_paste_requested.emit()
                return True
                
            # Delete: 삭제
            elif key == Qt.Key_Delete:
                self._on_delete_clicked()
                return True
                
        return super().eventFilter(obj, event)
        
    # UI 업데이트 메서드
    def clear_logic_list(self):
        """로직 목록 초기화"""
        self.logic_list.clear()
        
    def add_logic_item(self, logic_info, logic_id):
        """로직 아이템 추가"""
        item = QListWidgetItem(logic_info.get('name', ''))
        item.setData(Qt.UserRole, logic_id)
        self.logic_list.addItem(item)
        
    def update_logic_item(self, logic_id, logic_info):
        """로직 아이템 업데이트"""
        for i in range(self.logic_list.count()):
            item = self.logic_list.item(i)
            if item and item.data(Qt.UserRole) == logic_id:
                item.setText(logic_info.get('name', ''))
                break
                
    def remove_logic_item(self, logic_id):
        """로직 아이템 제거"""
        for i in range(self.logic_list.count()):
            item = self.logic_list.item(i)
            if item and item.data(Qt.UserRole) == logic_id:
                self.logic_list.takeItem(i)
                break
                
    def get_logic_count(self):
        """로직 아이템 개수 반환"""
        return self.logic_list.count()
        
    def get_logic_id_at(self, index):
        """특정 인덱스의 로직 ID 반환"""
        item = self.logic_list.item(index)
        return item.data(Qt.UserRole) if item else None
